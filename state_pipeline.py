"""Store tool-produced evidence in ADK session state without LLM transcription."""

from __future__ import annotations

import json
import re
import threading
from typing import Any, Mapping, MutableMapping

from . import __version__

from .config import BASELINE_SOURCE_KEYS, MAX_ADAPTIVE_QUERIES, MAX_PUBMED_QUERIES, MAX_PUBMED_RECORDS, MODEL
from .tools import (
    collect_baseline_evidence,
    normalize_sv_input,
    run_budgeted_adaptive_action,
    search_pubmed,
)


# ADK may execute multiple function calls from one model turn concurrently. The lock
# covers only state reservation and result merging, never an external network request.
_PIPELINE_STATE_LOCK = threading.Lock()


def normalize_and_store(raw_input: str, state: MutableMapping[str, Any]) -> dict[str, Any]:
    """Start a fresh investigation and preserve the normalizer's exact result."""
    result = normalize_sv_input(raw_input)
    # A new normalized input starts a new run in the same ADK session. Reset every
    # derived key together so evidence from the previous candidate cannot leak in.
    state["normalized_sv"] = result
    state["baseline_evidence"] = {"status": "pending"}
    state["adaptive_tool_results"] = []
    state["literature_tool_results"] = []
    state["literature_query_keys"] = []
    state["adaptive_investigation"] = {"status": "pending"}
    state["literature_evidence"] = {"status": "pending"}
    state["evidence_view"] = {"status": "pending"}
    state["verification_evidence_view"] = {"status": "pending"}
    state["verification_query_history"] = []
    state["verification_loaded_ids"] = []
    state["claim_synthesis"] = {"status": "pending"}
    state["verification"] = {"status": "pending"}
    state["final_report"] = {"status": "pending"}
    state["temp:adaptive_action_history"] = []
    state["temp:adaptive_query_count"] = 0
    return result


def baseline_and_store(state: MutableMapping[str, Any]) -> dict[str, Any]:
    """Run the unchanged baseline tools using the stored candidate, not LLM text."""
    sv = state.get("normalized_sv")
    if not isinstance(sv, dict) or sv.get("status") != "valid":
        result = {"status": "blocked", "reason": "input_validation_failed"}
    else:
        result = collect_baseline_evidence(json.dumps(sv, ensure_ascii=False))
    state["baseline_evidence"] = result
    return result


def adaptive_and_store(
    action: str,
    evidence_gap: str,
    reason: str,
    expected_information_gain: str,
    state: MutableMapping[str, Any],
) -> dict[str, Any]:
    """Preserve every tool audit and result, including failures and rejections."""
    sv = state.get("normalized_sv")
    if not isinstance(sv, dict) or sv.get("status") != "valid":
        result = {"status": "rejected", "action": action, "error": "input_validation_failed"}
    else:
        result = run_budgeted_adaptive_action(
            normalized_sv_json=json.dumps(sv, ensure_ascii=False),
            action=action,
            evidence_gap=evidence_gap,
            reason=reason,
            expected_information_gain=expected_information_gain,
            state=state,
        )
    with _PIPELINE_STATE_LOCK:
        history = list(state.get("adaptive_tool_results", []))
        history.append(result)
        state["adaptive_tool_results"] = history
    return result


def literature_and_store(
    query: str, max_records: int, state: MutableMapping[str, Any]
) -> dict[str, Any]:
    """Bound PubMed queries and store unique citations with available abstracts."""
    sv = state.get("normalized_sv")
    if not isinstance(sv, dict) or sv.get("status") != "valid":
        return {"source": "PubMed", "status": "blocked", "reason": "input_validation_failed"}

    normalized_query = re.sub(r"\s+", " ", query.strip())
    query_key = normalized_query.casefold()
    with _PIPELINE_STATE_LOCK:
        used_keys = list(state.get("literature_query_keys", []))
        if not query_key:
            rejection_reason = "empty_query"
        elif query_key in used_keys:
            rejection_reason = "duplicate_query"
        elif len(used_keys) >= MAX_PUBMED_QUERIES:
            rejection_reason = "query_budget_exhausted"
        else:
            rejection_reason = None
        if rejection_reason is not None:
            return {
                "source": "PubMed", "status": "rejected",
                "reason": rejection_reason,
                "query_budget": MAX_PUBMED_QUERIES,
                "queries_used": len(used_keys),
                "queries_remaining": max(
                    0, MAX_PUBMED_QUERIES - len(used_keys)
                ),
            }

        # Reserve before the request so parallel calls cannot reuse this query or
        # overrun the hard limit. API failures intentionally keep their reservation.
        used_keys.append(query_key)
        state["literature_query_keys"] = used_keys
    per_query_limit = max(1, min(max_records, MAX_PUBMED_RECORDS))
    result = search_pubmed(normalized_query, per_query_limit)
    with _PIPELINE_STATE_LOCK:
        history = list(state.get("literature_tool_results", []))
        seen_pmids = {
            str(record["pmid"])
            for previous in history
            for record in previous.get("records", [])
            if isinstance(record, dict) and record.get("pmid")
        }
        unique_records = []
        duplicates = 0
        for record in (result.get("records") or [])[:per_query_limit]:
            if not isinstance(record, dict) or not record.get("pmid"):
                continue
            pmid = str(record["pmid"])
            if pmid in seen_pmids:
                duplicates += 1
                continue
            seen_pmids.add(pmid)
            record["evidence_id"] = f"PMID-{pmid}"
            unique_records.append(record)
        if "records" in result:
            result["records"] = unique_records
        current_used = len(state.get("literature_query_keys", []))
        result.update({
            "query": normalized_query,
            "query_budget": MAX_PUBMED_QUERIES,
            "queries_used": current_used,
            "queries_remaining": MAX_PUBMED_QUERIES - current_used,
            "duplicate_pmids_excluded": duplicates,
            "returned_record_count": len(unique_records),
        })
        history.append(result)
        state["literature_tool_results"] = history
    return result


_EVIDENCE_SOURCES = {
    "CCRE-": "ENCODE cCRE",
    "REG-": "GeneHancer",
    "QTL-": "GTEx molecular QTL",
    "MAP-": "Reference mappability",
    "ENS-": "Ensembl",
    "VEP-": "Ensembl VEP",
    "GNO-": "gnomAD-SV",
    "CGD-": "ClinGen Dosage",
    "CLV-": "ClinVar",
    "DBV-": "dbVar",
    "DGV-": "DGV Gold",
    "PMID-": "PubMed",
    "INPUT-": "Normalized input",
    "QC-": "Artifact-risk rules",
}
_MATCH_TYPES = {
    "exact", "high_similarity", "partial_overlap", "region_search",
    "region_overlap", "nearby", "gene_level", "contextual", "not_applicable",
}
_REPORT_EVIDENCE_GROUPS = (
    "statistical_signals", "gene_region_annotation", "population_evidence",
    "clinical_phenotype_evidence", "literature_evidence",
    "artifact_risks", "possible_interpretations", "verified_claims",
)
_VERIFIED_REPORT_SECTIONS = (
    "gene_region_annotation", "population_evidence",
    "clinical_phenotype_evidence", "literature_evidence",
    "possible_interpretations",
)


def _input_statistic_items(normalized: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """Use one ordering for agent evidence and final report statistics."""
    statistics = normalized.get("statistics") or {}
    quality = normalized.get("quality") or {}
    statistics = statistics if isinstance(statistics, dict) else {}
    quality = quality if isinstance(quality, dict) else {}
    items = sorted(statistics.items())
    items.extend(sorted(
        (key, value) for key, value in quality.items()
        if (key == "call_rate" or key.startswith("call_rate_")) and key not in statistics
    ))
    return items


def _evidence_index(state: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Find tool-owned evidence records and retain their nearest source metadata."""
    found: dict[str, dict[str, Any]] = {}

    def visit(value: Any, inherited: Mapping[str, Any]) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item, inherited)
            return
        if not isinstance(value, dict):
            return
        context = dict(inherited)
        for key in ("status", "retrieved_at", "limitations", "match_type"):
            if key in value:
                context[key] = value[key]
        evidence_id = value.get("evidence_id")
        if isinstance(evidence_id, str):
            found.setdefault(evidence_id, {"record": value, "context": context})
        for child in value.values():
            visit(child, context)

    for key in ("baseline_evidence", "adaptive_tool_results", "literature_tool_results"):
        visit(state.get(key), {})

    normalized = state.get("normalized_sv")
    if isinstance(normalized, dict):
        if normalized.get("statistical_context"):
            evidence_id = "INPUT-STAT-CONTEXT"
            found[evidence_id] = {
                "record": {
                    "evidence_id": evidence_id,
                    "record_id": "statistical_context",
                    "summary": normalized["statistical_context"],
                },
                "context": {"status": "found"},
            }
        for index, (field, value) in enumerate(_input_statistic_items(normalized), start=1):
            evidence_id = f"INPUT-STAT-{index:03d}"
            found[evidence_id] = {
                "record": {
                    "evidence_id": evidence_id,
                    "record_id": field,
                    "field": field,
                    "value": value,
                    "summary": f"Input statistic {field}: {value}",
                },
                "context": {"status": "found"},
            }

    baseline = state.get("baseline_evidence")
    risks = (
        baseline.get("artifact_risk", {}).get("risk_items", [])
        if isinstance(baseline, dict)
        else []
    )
    for index, risk in enumerate(risks, start=1):
        if not isinstance(risk, dict):
            continue
        evidence_id = f"QC-BL-{index:03d}"
        found[evidence_id] = {
            "record": {**risk, "evidence_id": evidence_id},
            "context": {"status": "found"},
        }
    return found


_DROP = object()
_AUDIT_SCALARS = {
    "status", "source", "action", "evidence_gap", "reason",
    "expected_information_gain", "error", "completeness", "truncated",
    "records_truncated", "retrieved_at", "dataset", "backend",
    "consequence_count", "overall_risk", "query", "query_budget",
    "queries_used", "queries_remaining", "duplicate_pmids_excluded",
    "returned_record_count", "collection_policy", "matching_scope",
    "search_results_truncated", "search_uid_count", "compatible_record_count",
}
_AUDIT_VALUES = {"errors", "query_errors", "counts", "limitations", "attempts",
                 "query_region", "query_regions", "search_counts", "feature", "role"}


def _without_evidence_records(value: Any) -> Any:
    """Copy audit metadata while moving evidence records into the ID index."""
    if isinstance(value, dict):
        if isinstance(value.get("evidence_id"), str):
            return _DROP
        return {
            key: cleaned
            for key, item in value.items()
            if (cleaned := _without_evidence_records(item)) is not _DROP
        }
    if isinstance(value, list):
        return [
            cleaned
            for item in value
            if (cleaned := _without_evidence_records(item)) is not _DROP
        ]
    return value


def _audit_context(value: Any) -> Any:
    """Keep source status and limitations, not bulky query plumbing."""
    if isinstance(value, list):
        return [cleaned for item in value if (cleaned := _audit_context(item))]
    if not isinstance(value, dict) or isinstance(value.get("evidence_id"), str):
        return {}
    result = {}
    for key, item in value.items():
        if key in _AUDIT_SCALARS | _AUDIT_VALUES:
            result[key] = _without_evidence_records(item)
        elif isinstance(item, (dict, list)) and (cleaned := _audit_context(item)):
            result[key] = cleaned
    return result


def build_evidence_view(
    state: Mapping[str, Any], evidence_ids: set[str] | None = None
) -> dict[str, Any]:
    """Build the single deterministic evidence projection shown to later LLMs.

    Full tool results remain untouched in state. Records occur once in this view,
    keyed by their real evidence ID; source/audit metadata is retained separately
    without duplicating those records.
    """
    complete_index = _evidence_index(state)
    index = (
        complete_index
        if evidence_ids is None
        else {key: value for key, value in complete_index.items() if key in evidence_ids}
    )
    return {
        "status": "ready",
        "record_count": len(index),
        "total_record_count": len(complete_index),
        "records_by_id": {
            evidence_id: item["record"] for evidence_id, item in sorted(index.items())
        },
        "source_context": {
            key: _audit_context(state.get(key))
            for key in (
                "baseline_evidence",
                "adaptive_tool_results",
                "literature_tool_results",
            )
        },
    }


def _evidence_directory_row(evidence_id: str, indexed: Mapping[str, Any]) -> dict[str, Any]:
    record = indexed["record"]
    row = {"evidence_id": evidence_id, "source_prefix": evidence_id.split("-", 1)[0]}
    for key in ("feature_type", "breakpoint_role", "query_scope", "scope", "match_type",
                "chrom", "seq_region_name", "start", "end", "description", "external_name",
                "geneName", "gene_symbol", "geneSymbol", "record_id", "title", "field"):
        value = record.get(key)
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            row[key] = value[:160] if isinstance(value, str) else value
    return row


def prepare_verification_evidence(state: MutableMapping[str, Any]) -> dict[str, Any]:
    """Keep the full view in state, expose a bounded discovery directory instead."""
    index = _evidence_index(state)
    state["evidence_view"] = build_evidence_view(state)
    claims = _json_object(state.get("claim_synthesis")).get("candidate_claims", [])
    cited = sorted({eid for c in claims if isinstance(c, dict)
                    for eid in c.get("evidence_ids", []) if isinstance(eid, str)})
    directory = [_evidence_directory_row(eid, item) for eid, item in sorted(index.items())]
    visible = []
    directory_size = 0
    for row in directory[:80]:
        directory_size += len(json.dumps(row, ensure_ascii=False))
        if directory_size > 12_000:
            break
        visible.append(row)
    result = {"total_record_count": len(index), "cited_ids": cited,
              "unknown_cited_ids": [eid for eid in cited if eid not in index],
              "directory": visible, "directory_truncated": len(directory) > len(visible),
              "source_counts": {prefix: sum(r["source_prefix"] == prefix for r in directory)
                                for prefix in sorted({r["source_prefix"] for r in directory})},
              "source_context": state["evidence_view"]["source_context"],
              "fetch_record_limit": 8, "search_page_limit": 20,
              "response_character_limit": 24_000}
    state["verification_evidence_view"] = result
    state["verification_query_history"] = []
    state["verification_loaded_ids"] = []
    return result


def query_verification_evidence(
    state: MutableMapping[str, Any], *, evidence_ids: list[str] | None = None,
    fields: list[str] | None = None, source_prefix: str = "", feature_type: str = "",
    scope: str = "", text: str = "", chrom: str = "", start: int = 0, end: int = 0,
    offset: int = 0, limit: int = 20,
) -> dict[str, Any]:
    """Deterministic, bounded, read-only lookup over stored evidence; no network."""
    ids, paths = evidence_ids or [], fields or []
    if ((evidence_ids is not None and not isinstance(evidence_ids, list))
        or (fields is not None and not isinstance(fields, list))
        or not isinstance(ids, list) or not isinstance(paths, list)
        or any(not isinstance(v, str) or not v or len(v) > 160 for v in ids + paths)
        or len(ids) > 8 or len(paths) > 20
        or any(not isinstance(v, str) or len(v) > 160 for v in (source_prefix, feature_type, scope, text, chrom))
        or any(not isinstance(v, int) or isinstance(v, bool) for v in (start, end, offset, limit))
        or offset < 0 or not 1 <= limit <= 20
        or ((start or end) and (not chrom or start < 1 or end < start))
        or (ids and any((source_prefix, feature_type, scope, text, chrom, start, end, offset)))
        or (paths and not ids)):
        return {"status": "rejected", "error": "invalid_lookup_arguments"}
    with _PIPELINE_STATE_LOCK:
        history = list(state.get("verification_query_history", []))
        audit = {"query_number": len(history) + 1, "mode": "fetch" if ids else "search",
                 "evidence_ids": ids, "fields": paths, "source_prefix": source_prefix,
                 "feature_type": feature_type, "scope": scope, "text": text,
                 "chrom": chrom, "start": start, "end": end, "offset": offset, "limit": limit}
        request = {key: value for key, value in audit.items() if key != "query_number"}
        request.update(evidence_ids=sorted(set(ids)), fields=sorted(set(paths)),
                       text=text.casefold(), chrom=chrom.removeprefix("chr"))
        request_key = json.dumps(request, sort_keys=True, ensure_ascii=False)
        previous = next((item for item in history if item.get("request_key") == request_key), None)
        if previous is not None:
            return {"status": "duplicate_request", "previous_query_number": previous["query_number"],
                    "returned_ids": previous.get("returned_ids", []),
                    "hint": "Use the earlier response. Change fields, filters, or page only when different evidence is needed."}
        audit["request_key"] = request_key
        state["verification_query_history"] = history + [audit]
    index = _evidence_index(state)
    result: dict[str, Any] = {"status": "complete", "records_by_id": {}, "errors": [],
                              "query_number": audit["query_number"]}
    if ids:
        for eid in dict.fromkeys(ids):
            if eid not in index:
                result["errors"].append({"evidence_id": eid, "error": "unknown_evidence_id"})
                continue
            record = index[eid]["record"]
            projection = {}
            for path in paths:
                value: Any = record
                try:
                    for key in path.split("."):
                        value = value[int(key)] if isinstance(value, list) and key.isdecimal() else value[key]
                    projection[path] = value
                except (KeyError, IndexError, TypeError):
                    result["errors"].append({"evidence_id": eid, "field": path, "error": "unknown_field_path"})
            entry = {"record": projection if paths else record, "context": index[eid]["context"],
                     "projection_fields": paths}
            if paths and not projection:
                continue
            result["records_by_id"][eid] = entry
            if len(json.dumps(result, ensure_ascii=False)) > 23_000:
                del result["records_by_id"][eid]
                result["errors"].append({"evidence_id": eid, "error": "response_size_limit",
                    "available_fields": list(record)[:40], "hint": "Fetch fewer IDs or select fields; dotted paths support list indices."})
    else:
        matches = []
        for eid, item in sorted(index.items()):
            row = _evidence_directory_row(eid, item)
            record = item["record"]
            if source_prefix and row["source_prefix"] != source_prefix:
                continue
            if feature_type and record.get("feature_type") != feature_type:
                continue
            if scope and scope not in {record.get(k) for k in ("scope", "query_scope", "breakpoint_role")}:
                continue
            if chrom and str(record.get("chrom") or record.get("seq_region_name") or "").removeprefix("chr") != chrom.removeprefix("chr"):
                continue
            if start and (not isinstance(record.get("start"), int) or not isinstance(record.get("end"), int)
                          or record["start"] > end or record["end"] < start):
                continue
            # Literal matching over the original JSON, not regex/fuzzy or LLM summaries.
            if text and text.casefold() not in json.dumps(record, ensure_ascii=False).casefold():
                continue
            matches.append(row)
        page = []
        page_size = 0
        for row in matches[offset:offset + limit]:
            page_size += len(json.dumps(row, ensure_ascii=False))
            if page_size > 20_000:
                break
            page.append(row)
        result.update(directory=page, total_matches=len(matches), offset=offset,
                      next_offset=offset + len(page) if offset + len(page) < len(matches) else None,
                      search_scope="stored_records_only", truncated=offset + len(page) < len(matches))
    if len(json.dumps(result, ensure_ascii=False)) > 24_000:
        # Keep an explicit failure instead of silently clipping record content.
        result = {"status": "partial", "records_by_id": {},
                  "errors": [{"error": "response_size_limit", "hint": "Fetch fewer IDs or fields."}],
                  "query_number": audit["query_number"]}
    if result["errors"]:
        result["status"] = "partial"
    with _PIPELINE_STATE_LOCK:
        loaded = set(state.get("verification_loaded_ids", [])) | set(result["records_by_id"])
        state["verification_loaded_ids"] = sorted(loaded)
        history = list(state["verification_query_history"])
        history[audit["query_number"] - 1] = {**audit, "status": result["status"],
            "returned_ids": list(result["records_by_id"]) or [r["evidence_id"] for r in result.get("directory", [])],
            "errors": result["errors"], "total_matches": result.get("total_matches"), "next_offset": result.get("next_offset")}
        state["verification_query_history"] = history
    return result


def _catalog_record(
    evidence_id: str, indexed: Mapping[str, Any], used_by: list[str]
) -> dict[str, Any]:
    """Project one raw record into a compact, source-aware catalog entry."""
    record = indexed["record"]
    context = indexed["context"]
    source = next(
        (name for prefix, name in _EVIDENCE_SOURCES.items() if evidence_id.startswith(prefix)),
        str(record.get("source") or "unknown"),
    )
    record_id = next(
        (record[key] for key in (
            "record_id", "variant_id", "transcript_id", "gene_id", "pmid", "id",
        ) if record.get(key) not in (None, "")),
        evidence_id,
    )
    limitations = context.get("limitations", "")
    if isinstance(limitations, list):
        limitations = "; ".join(map(str, limitations))
    match_type = record.get("match_type") or context.get("match_type")
    record_chrom = record.get("chrom") or record.get("seq_region_name")
    record_start = record.get("start", record.get("pos"))
    position = (
        f"{record_chrom}:{record_start}-{record.get('end')}"
        if record_chrom and record_start is not None and record.get("end") is not None
        else ""
    )

    def facts(*keys: str) -> dict[str, Any]:
        return {
            key: record[key] for key in keys
            if record.get(key) not in (None, "", [], {})
        }

    prefix = evidence_id.split("-", 1)[0]
    evidence_type = "source_record"
    finding_status = ""
    key_facts: dict[str, Any] = {}
    label = ""
    if prefix == "QC":
        evidence_type = "technical_qc"
        finding_status = str(record.get("status") or "unknown")
        key_facts = facts("risk_type", "evidence", "recommended_check")
        label = (
            f"{record.get('risk_type', 'Technical risk')}: {finding_status}. "
            f"{record.get('impact', '')}"
        )
    elif prefix == "INPUT":
        evidence_type = "input_statistic"
        finding_status = "reported"
        key_facts = facts("field", "value")
        label = str(record.get("summary") or f"{record_id}: {record.get('value')}")
    elif prefix == "ENS":
        evidence_type = "genomic_overlap"
        role = str(record.get("breakpoint_role") or "nominal")
        finding_status = "interval_overlap" if role == "nominal" else "breakpoint_window_hit"
        name = record.get("external_name") or record.get("id") or record_id
        key_facts = facts("feature_type", "breakpoint_role", "external_name", "id", "biotype")
        if position:
            key_facts["position"] = position
        label = f"{record.get('feature_type', 'Feature')} {name} found in the {role} region."
    elif prefix == "VEP":
        evidence_type = "predicted_consequence"
        finding_status = str(record.get("impact") or "predicted").lower()
        key_facts = facts(
            "gene_symbol", "gene_id", "transcript_id", "consequence_terms",
            "impact", "percentage_overlap", "canonical", "mane_select",
        )
        subject = record.get("gene_symbol") or record.get("transcript_id") or record_id
        terms = ", ".join(map(str, record.get("consequence_terms") or [])) or "consequence"
        label = f"VEP predicts {terms} for {subject} ({record.get('impact') or 'impact not provided'})."
    elif prefix == "GNO":
        evidence_type = "population_variant"
        finding_status = str(match_type or "candidate_match")
        key_facts = facts("variant_id", "type", "af", "ac", "an", "filters", "match_metrics")
        if position:
            key_facts["position"] = position
        label = f"gnomAD-SV {record_id} is a {match_type or 'candidate'} match"
        if record.get("af") is not None:
            label += f" (AF={record['af']})"
        label += "."
    elif prefix == "CGD":
        evidence_type = "dosage_curation"
        finding_status = str(record.get("relevant_assessment") or "curated_overlap")
        key_facts = facts(
            "entity", "entity_type", "relevant_dosage_direction",
            "relevant_assessment", "haploinsufficiency", "triplosensitivity",
        )
        if position:
            key_facts["position"] = position
        label = f"ClinGen dosage record for {record.get('entity') or record_id}: {finding_status}."
    elif prefix == "CLV":
        evidence_type = "clinical_record"
        finding_status = str(record.get("germline_classification") or "not_provided")
        key_facts = facts(
            "variant_type", "germline_classification", "review_status", "traits",
            "genes", "supporting_scv_count", "match_metrics",
        )
        if position:
            key_facts["position"] = position
        label = f"ClinVar {record_id}: {finding_status} ({record.get('review_status') or 'review status not provided'})."
    elif prefix == "DBV":
        evidence_type = "submitted_variant"
        finding_status = str(record.get("type_compatibility") or "submitted_record")
        key_facts = facts(
            "study_id", "variant_types", "type_compatibility", "clinical_significance",
            "genes", "methods", "match_metrics",
            "call_details",
        )
        if position:
            key_facts["position"] = position
        label = f"dbVar {record_id}: {finding_status} submitted variant record."
    elif prefix == "DGV":
        evidence_type = "population_cnv"
        finding_status = str(match_type or "candidate_match")
        key_facts = facts(
            "variant_type", "variant_sub_type", "frequency",
            "num_unique_samples_tested", "num_samples_with_variant",
            "num_studies", "match_metrics",
        )
        if position:
            key_facts["position"] = position
        label = f"DGV Gold {record_id}: {match_type or 'candidate'} population CNV record."
    elif prefix in {"CCRE", "REG", "QTL", "MAP"}:
        evidence_type = {"CCRE": "regulatory_overlap", "REG": "regulatory_gene_link",
                         "QTL": "regional_qtl_context", "MAP": "reference_mappability"}[prefix]
        finding_status = str(record.get("query_scope") or record.get("scope") or "found")
        key_facts = facts(
            "genome_build", "query_scope", "scope", "window_source", "cCRE_class",
            "DNase_maxZ", "H3K4me3_maxZ", "H3K27ac_maxZ", "CTCF_maxZ",
            "geneHancerIdentifier", "geneName", "geneId", "genePos",
            "geneAssociationMethods", "value", "eqtlName", "eqtlPos", "tissue",
            "pip", "clusterPip", "sv_identity", "ld_with_sv", "track", "kmer_length",
            "qtl_type", "variantId", "ref", "alt", "geneSymbol", "gencodeId",
            "tissueSiteDetailId", "phenotypeId", "pValue", "nes", "datasetId",
            "coverage_fraction", "covered_bases", "unmeasured_bases", "mean", "minimum",
            "fraction_below_one_of_measured_bases",
        )
        if position:
            key_facts["position"] = position
        label = f"{source} {record_id}: {evidence_type} ({finding_status})."
    elif prefix == "PMID":
        evidence_type = "literature_abstract" if record.get("abstract") else "literature_metadata"
        finding_status = "citation_found"
        key_facts = facts("authors", "author_count", "source", "pubdate", "doi",
                          "abstract_status", "abstract", "abstract_source_url", "abstract_error")
        label = str(record.get("title") or f"PubMed record {record_id}")
    else:
        label = str(next(
            (record[key] for key in ("summary", "title", "description", "interpretation") if record.get(key)),
            f"{source} record {record_id}",
        ))
    return {
        "evidence_id": evidence_id,
        "source": source,
        "evidence_type": evidence_type,
        "retrieval_status": context.get("status")
        if context.get("status") in {
            "found", "not_found", "not_applicable", "unavailable", "error", "not_queried",
        }
        else "found",
        "finding_status": finding_status,
        "record_id": str(record_id),
        "match_type": match_type if match_type in _MATCH_TYPES and match_type != "contextual" else None,
        "summary": label.strip()[:500],
        "key_facts": key_facts,
        "used_by": used_by,
        "source_url": str(record.get("source_url") or record.get("url") or ""),
        "retrieved_at": str(record.get("retrieved_at") or context.get("retrieved_at") or ""),
        "limitations": str(limitations)[:1000],
    }


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    text = value.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _deduplicate_strings(*groups: Any) -> list[str]:
    return list(dict.fromkeys(
        str(item)
        for group in groups
        if isinstance(group, list)
        for item in group
        if item not in (None, "")
    ))


def reconcile_verification_from_state(
    verification: Mapping[str, Any], state: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind verifier verdicts back to the exact synthesis claims.

    The verifier may judge claims but cannot add or rewrite their identity, wording,
    section, type, or evidence links. The program corrects input-only database_fact
    labels to observation independently of the verifier.
    """
    synthesis = _json_object(state.get("claim_synthesis"))
    candidates = {
        claim["claim_id"]: claim
        for claim in synthesis.get("candidate_claims", [])
        if isinstance(claim, dict) and isinstance(claim.get("claim_id"), str)
    }
    supported: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    warnings = _deduplicate_strings(verification.get("warnings"))
    evidence_index = _evidence_index(state)
    seen: set[str] = set()
    valid_statuses = {
        "supported", "partially_supported", "unsupported", "conflicting"
    }
    # A rejection takes precedence if the verifier also lists the same claim as supported.
    for rejected_by_verifier, verdict in (
        [(True, item) for item in verification.get("rejected_claims") or []]
        + [(False, item) for item in verification.get("supported_claims") or []]
    ):
        if not isinstance(verdict, dict):
            continue
        claim_id = verdict.get("claim_id")
        candidate = candidates.get(claim_id)
        status = verdict.get("verification_status")
        if candidate is None or claim_id in seen or status not in valid_statuses:
            warnings.append(f"Discarded invalid verifier verdict for claim {claim_id!r}.")
            continue
        seen.add(claim_id)
        bound = {
            "claim_id": claim_id,
            "text": candidate.get("text", ""),
            "claim_type": candidate.get("claim_type", "observation"),
            "report_section": candidate.get("report_section"),
            "evidence_ids": list(candidate.get("evidence_ids") or []),
            "confidence": verdict.get("confidence", "unknown"),
            "verification_status": status,
            "notes": str(verdict.get("notes") or ""),
        }
        if rejected_by_verifier and status in {"supported", "partially_supported"}:
            note = (
                f"Not approved: verifier placed claim {claim_id} in rejected_claims "
                f"with status {status}."
            )
            bound["verification_status"] = status = "unsupported"
            bound["confidence"] = "unknown"
            bound["notes"] = "; ".join(filter(None, (bound["notes"], note)))
            warnings.append(note)
        if (
            bound["claim_type"] == "database_fact"
            and bound["evidence_ids"]
            and all(eid in evidence_index and eid.startswith("INPUT-") for eid in bound["evidence_ids"])
        ):
            bound["claim_type"] = "observation"
            warnings.append(f"Corrected input-only database_fact {claim_id} to observation.")
        if state.get("verification_evidence_view", {}).get("fetch_record_limit") and status in {"supported", "partially_supported"}:
            unread = sorted(set(bound["evidence_ids"]) - set(state.get("verification_loaded_ids", [])))
            if unread:
                bound["verification_status"] = status = "unsupported"
                bound["confidence"] = "unknown"
                bound["notes"] = "Not verified: cited records were not fetched: " + ", ".join(unread)
                warnings.append(f"Claim {claim_id} was not verified because cited records were not fetched.")
        if bound["claim_type"] == "hypothesis" and status in {"supported", "partially_supported"}:
            changed = status != "partially_supported" or bound["confidence"] != "low"
            bound["verification_status"] = status = "partially_supported"
            bound["confidence"] = "low"
            note = "A hypothesis is not an established finding."
            if note not in bound["notes"]:
                bound["notes"] = "; ".join(filter(None, (bound["notes"], note)))
            if changed:
                warnings.append(f"Conservatively qualified claim {claim_id}: {note}")
        if status == "supported":
            records = [
                evidence_index[evidence_id]["record"]
                for evidence_id in bound["evidence_ids"]
                if evidence_id in evidence_index
            ]
            note = None
            if bound["claim_type"] == "inference" and re.search(
                r"\b(benign|pathogenic|neutral|harmless|deleterious|"
                r"disease-causing|no (?:adverse |functional )?effect)\b",
                bound["text"],
                re.IGNORECASE,
            ):
                note = (
                    "Available evidence does not establish a clinical or "
                    "functional classification."
                )
                bound["confidence"] = "low"
            elif re.search(
                r"\b(corresponds?|matches?|same variant|identical)\b",
                bound["text"],
                re.IGNORECASE,
            ) and not any(
                record.get("match_type") in {"exact", "high_similarity"}
                for record in records
            ):
                note = (
                    "Cited database records do not establish an exact or "
                    "high-similarity match."
                )
                if bound["confidence"] == "high":
                    bound["confidence"] = "medium"
            if note:
                bound["verification_status"] = status = "partially_supported"
                bound["notes"] = "; ".join(filter(None, (bound["notes"], note)))
                warnings.append(f"Conservatively qualified claim {claim_id}: {note}")
        (supported if status in {"supported", "partially_supported"} else rejected).append(
            bound
        )

    missing = sorted(set(candidates) - seen)
    if missing:
        warnings.append("Verifier did not adjudicate candidate claims: " + ", ".join(missing))
    approved = {}
    for field in ("evidence_gaps", "limitations"):
        originals = _deduplicate_strings(synthesis.get(field))
        requested = _deduplicate_strings(verification.get("approved_" + field))
        approved["approved_" + field] = [item for item in requested if item in originals]
        if any(item not in originals for item in requested):
            warnings.append(f"Discarded verifier-added or rewritten {field}; only exact synthesis items are allowed.")
    return {
        "publication_allowed": bool(verification.get("publication_allowed")) and not missing,
        "supported_claims": supported,
        "rejected_claims": rejected,
        "contradictions": list(verification.get("contradictions") or []),
        "missing_evidence": list(verification.get("missing_evidence") or []),
        "warnings": list(dict.fromkeys(warnings)),
        **approved,
    }


def _source_status(status: Any) -> str:
    if status in {
        "found", "not_found", "not_applicable", "unavailable", "error", "not_queried"
    }:
        return str(status)
    if status in {"complete", "partial"}:
        return "found"
    return "not_queried"


def _query_audit_row(source: Mapping[str, Any], stage: str, action: str = "") -> dict[str, Any]:
    """Project query facts without interpreting zero hits or treating truncation as failure."""
    details = {
        field: source[field]
        for field in ("dataset", "query", "query_region", "query_regions", "query_strategy",
                      "feature", "role", "error", "query_errors")
        if source.get(field) not in (None, "", [], {})
    }
    counts = {key: value for key, value in (source.get("counts") or {}).items()
              if type(value) is int}
    counts.update({key: source[key] for key in (
        "search_uid_count", "compatible_record_count", "returned_record_count",
        "raw_region_record_count", "consequence_count",
    ) if type(source.get(key)) is int})
    searches = source.get("search_counts") or []
    if searches and all(type(item.get("total_count")) is int for item in searches):
        counts["search_hit_count_across_queries"] = sum(item["total_count"] for item in searches)
    if "returned_record_count" not in counts and isinstance(source.get("records"), list):
        counts["returned_record_count"] = len(source["records"])
    flags = []
    for key in ("truncated", "records_truncated", "search_results_truncated"):
        value = source.get(key)
        values = value.values() if isinstance(value, dict) else [value]
        flags.extend(flag for flag in values if isinstance(flag, bool))
    flags.extend(item["search_truncated"] for item in searches if isinstance(item.get("search_truncated"), bool))
    return {
        "source": str(source.get("source") or "Unknown"),
        "status": _source_status(source.get("status")),
        "query_summary": json.dumps(details, ensure_ascii=False),
        "retrieved_at": str(source.get("retrieved_at") or ""),
        "stage": stage, "action": action,
        "completeness": str(source.get("completeness") or ""),
        "truncated": any(flags) if flags else None,
        "counts": counts,
    }


def _query_provenance(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    baseline = state.get("baseline_evidence")
    rows: list[dict[str, Any]] = []
    if isinstance(baseline, dict):
        for key in BASELINE_SOURCE_KEYS.values():
            source = baseline.get(key)
            if not isinstance(source, dict):
                continue
            rows.append(_query_audit_row(source, "baseline"))
    for item in state.get("adaptive_tool_results", []):
        if not isinstance(item, dict):
            continue
        wrapper = item.get("result")
        result = wrapper.get("result", {}) if isinstance(wrapper, dict) else {}
        if not isinstance(result, dict):
            continue
        for scope in result.get("results") or [result]:
            if isinstance(scope, dict):
                rows.append(_query_audit_row({
                    "source": result.get("source"), "retrieved_at": result.get("retrieved_at"),
                    **scope,
                }, "adaptive", str(item.get("action") or "")))
    for result in state.get("literature_tool_results", []):
        if isinstance(result, dict):
            rows.append(_query_audit_row(result, "literature"))
    return rows


def _investigation_log(verification: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    actions = []
    for item in state.get("adaptive_tool_results", []):
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        normalized_status = status if status in {"executed", "rejected"} else "not_executed"
        actions.append({
            "action": str(item.get("action") or "unknown"),
            "evidence_gap": str(item.get("evidence_gap") or ""),
            "reason": str(item.get("reason") or ""),
            "expected_information_gain": str(item.get("expected_information_gain") or ""),
            "status": normalized_status,
            "result_status": str(item.get("result_status") or ""),
            "rejection_reason": str(item.get("rejection_reason") or ""),
        })
    # Planning text stays in the action audit, not in published biological conclusions.
    stop_reason = (
        "Recorded adaptive follow-ups finished. No further follow-up was executed."
        if any(item["status"] == "executed" for item in actions)
        else "No adaptive follow-up was executed."
    )
    return {
        "identified_evidence_gaps": verification["approved_evidence_gaps"],
        "planned_actions": [dict(item, status="planned") for item in actions],
        "executed_actions": actions,
        "query_budget": MAX_ADAPTIVE_QUERIES,
        "queries_used": sum(item["status"] == "executed" for item in actions),
        "stop_reason": str(stop_reason),
        "remaining_limitations": verification["approved_limitations"],
    }


def finalize_report_from_state(
    report: dict[str, Any], state: Mapping[str, Any]
) -> dict[str, Any]:
    """Replace every mechanically derivable report field from session state.

    Verified claims, tool audits, and verifier-approved synthesis text determine
    substantive report content. Model drafts cannot bypass the approval boundary.
    """
    report = dict(report)
    report["model"] = MODEL
    normalized = state.get("normalized_sv")
    normalized = normalized if isinstance(normalized, dict) else {}
    summary_fields = {
        "sv_id", "genome_build", "genome_build_original", "chrom", "start", "end",
        "coordinate_system", "chromosome_length_bp", "cipos", "ciend",
        "start_confidence_interval", "end_confidence_interval",
        "breakpoint_uncertainty_status", "imprecise", "bnd_mate_status",
        "mate_chrom", "mate_pos", "mate_confidence_interval", "local_orientation",
        "mate_orientation", "sv_type", "sv_type_original", "sv_subtype", "length_bp",
    }
    report["sv_summary"] = {
        "validation_status": (
            "valid" if normalized.get("status") == "valid" else "validation_error"
        ),
        **{key: normalized[key] for key in summary_fields if key in normalized},
    }
    report["statistical_context"] = normalized.get("statistical_context") or ""
    report["statistical_signals"] = [
        {
            "statement": f"{field}: {value}",
            "evidence_ids": [f"INPUT-STAT-{index:03d}"],
            "confidence": "unknown",
            "kind": "observation",
        }
        for index, (field, value) in enumerate(
            _input_statistic_items(normalized), start=1
        )
    ]
    baseline = state.get("baseline_evidence")
    baseline = baseline if isinstance(baseline, dict) else {}
    risks = baseline.get("artifact_risk", {}).get("risk_items", [])
    report["artifact_risks"] = [
        {
            "risk_type": str(item.get("risk_type") or "unknown"),
            "status": item.get("status")
            if item.get("status") in {"present", "absent", "unknown"}
            else "unknown",
            "impact": str(item.get("impact") or ""),
            "evidence": item.get("evidence"),
            "evidence_ids": [f"QC-BL-{index:03d}"],
            "recommended_check": str(item.get("recommended_check") or ""),
        }
        for index, item in enumerate(risks, start=1)
        if isinstance(item, dict)
    ]
    verification = reconcile_verification_from_state(_json_object(state.get("verification")), state)
    report["verified_claims"] = list(verification.get("supported_claims") or [])
    report["contradictions"] = list(verification.get("contradictions") or [])
    report["investigation_log"] = _investigation_log(verification, state)
    report["query_provenance"] = _query_provenance(state)
    report["report_version"] = __version__
    source_failures = [
        f"{source['source']} {source['stage']} query was incomplete "
        f"({'truncated' if source.get('truncated') else source.get('completeness') or source['status']}); "
        f"scope: {source['query_summary']}."
        for source in report["query_provenance"]
        if (
            source.get("status") in {"error", "unavailable"}
            or source.get("completeness") in {"partial", "failed"}
            or source.get("truncated") is True
        )
    ]
    if baseline.get("status") in {"pending", "blocked", "error"}:
        source_failures.append("Required baseline collection did not finish; no complete retrieval is established.")
    if normalized.get("status") != "valid":
        report["report_status"] = "blocked"
    elif verification.get("publication_allowed") is False or source_failures:
        report["report_status"] = "incomplete"
    else:
        report["report_status"] = "complete"
    report["limitations"] = _deduplicate_strings(
        baseline.get("limitations"),
        verification.get("approved_limitations"),
        verification.get("missing_evidence"),
        verification.get("warnings"),
        source_failures,
    )

    # Factual sections require exact support. Possible interpretations may retain
    # qualified inferences/hypotheses, without upgrading them to established facts.
    for section in _VERIFIED_REPORT_SECTIONS:
        report[section] = []
    for claim in verification.get("supported_claims", []):
        section = claim.get("report_section")
        status = claim.get("verification_status")
        qualified_interpretation = (
            section == "possible_interpretations"
            and claim.get("claim_type") in {"inference", "hypothesis"}
            and status == "partially_supported"
            and bool(claim.get("notes"))
        )
        if section not in report or (status != "supported" and not qualified_interpretation):
            continue
        report[section].append({
            "statement": claim.get("text", ""),
            "evidence_ids": list(claim.get("evidence_ids") or []),
            "confidence": claim.get("confidence", "unknown"),
            "kind": claim.get("claim_type", "observation"),
            "verification_status": status,
            "qualification": claim.get("notes", "") if qualified_interpretation else "",
        })

    next_step_gaps = _deduplicate_strings(
        verification.get("approved_evidence_gaps"), verification.get("missing_evidence")
    )
    report["recommended_next_steps"] = (
        [f"Resolve evidence gap: {gap}" for gap in next_step_gaps]
        if next_step_gaps
        else [
            "Review the verified claims, limitations, and source records before "
            "clinical or experimental use."
        ]
    )

    index = _evidence_index(state)
    unknown: set[str] = set()
    referenced: set[str] = set()
    used_by: dict[str, list[str]] = {}

    for group in _REPORT_EVIDENCE_GROUPS:
        items = report.get(group)
        if not isinstance(items, list):
            continue
        cleaned = []
        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict) or not isinstance(item.get("evidence_ids"), list):
                cleaned.append(item)
                continue
            original = [value for value in item["evidence_ids"] if isinstance(value, str)]
            known = [value for value in original if value in index]
            unknown.update(set(original) - set(known))
            if original and not known:
                continue
            item = dict(item)
            item["evidence_ids"] = known
            referenced.update(known)
            item_name = item.get("claim_id") or item.get("risk_type")
            location = f"{group}.{item_name}" if item_name else f"{group}[{item_index}]"
            for evidence_id in known:
                used_by.setdefault(evidence_id, []).append(location)
            cleaned.append(item)
        report[group] = cleaned

    report["evidence_catalog"] = [
        _catalog_record(
            evidence_id, index[evidence_id], list(dict.fromkeys(used_by.get(evidence_id, [])))
        )
        for evidence_id in sorted(referenced)
    ]
    if unknown:
        limitations = list(report.get("limitations") or [])
        limitations.append(
            "Removed report references absent from tool-owned session evidence: "
            + ", ".join(sorted(unknown))
        )
        report["limitations"] = limitations
    return report
