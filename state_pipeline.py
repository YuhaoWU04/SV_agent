"""Store tool-produced evidence in ADK session state without LLM transcription."""

from __future__ import annotations

import json
import re
import threading
from typing import Any, Mapping, MutableMapping

from .config import MAX_ADAPTIVE_QUERIES, MAX_PUBMED_QUERIES, MAX_PUBMED_RECORDS
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
    """Bound PubMed queries and store unique, compact citation metadata."""
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
        statistics = normalized.get("statistics")
        if isinstance(statistics, dict):
            for index, (field, value) in enumerate(sorted(statistics.items()), start=1):
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
}
_AUDIT_VALUES = {"errors", "query_errors", "counts", "limitations", "attempts"}


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


def _catalog_record(evidence_id: str, indexed: Mapping[str, Any]) -> dict[str, Any]:
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
    label = next(
        (record[key] for key in (
            "summary", "title", "description", "interpretation", "external_name",
            "gene_symbol", "risk_type", "field",
        ) if record.get(key)),
        None,
    )
    limitations = context.get("limitations", "")
    if isinstance(limitations, list):
        limitations = "; ".join(map(str, limitations))
    match_type = record.get("match_type") or context.get("match_type")
    return {
        "evidence_id": evidence_id,
        "source": source,
        "status": context.get("status")
        if context.get("status") in {
            "found", "not_found", "not_applicable", "unavailable", "error", "not_queried",
        }
        else "found",
        "record_id": str(record_id),
        "match_type": match_type if match_type in _MATCH_TYPES else "contextual",
        "support_direction": "contextual",
        "summary": str(label or f"{source} record {record_id}")[:500],
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
    section, type, or evidence links.
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
    for verdict in (
        list(verification.get("supported_claims") or [])
        + list(verification.get("rejected_claims") or [])
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
        if status == "supported":
            records = [
                evidence_index[evidence_id]["record"]
                for evidence_id in bound["evidence_ids"]
                if evidence_id in evidence_index
            ]
            note = None
            if bound["claim_type"] == "hypothesis":
                note = "A hypothesis is not an established finding."
                bound["confidence"] = "low"
            elif bound["claim_type"] == "inference" and re.search(
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
            elif records and all(
                evidence_id.startswith("PMID-")
                for evidence_id in bound["evidence_ids"]
            ):
                note = (
                    "Only PubMed citation metadata was retrieved; full-text "
                    "support was not checked."
                )
                if bound["confidence"] == "high":
                    bound["confidence"] = "medium"
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
    return {
        "publication_allowed": bool(verification.get("publication_allowed")) and not missing,
        "supported_claims": supported,
        "rejected_claims": rejected,
        "contradictions": list(verification.get("contradictions") or []),
        "missing_evidence": list(verification.get("missing_evidence") or []),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _source_status(status: Any) -> str:
    if status in {
        "found", "not_found", "not_applicable", "unavailable", "error", "not_queried"
    }:
        return str(status)
    if status in {"complete", "partial"}:
        return "found"
    return "not_queried"


def _query_provenance(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    baseline = state.get("baseline_evidence")
    rows: list[dict[str, Any]] = []
    if isinstance(baseline, dict):
        for key in (
            "region_annotation", "vep_evidence", "database_evidence",
            "clingen_dosage_evidence", "clinvar_evidence", "dbvar_evidence",
            "dgv_evidence",
        ):
            source = baseline.get(key)
            if not isinstance(source, dict):
                continue
            details = {
                field: source[field]
                for field in ("dataset", "query_region", "query_regions", "query_strategy")
                if source.get(field) not in (None, "", [])
            }
            rows.append({
                "source": str(source.get("source") or key),
                "status": _source_status(source.get("status")),
                "query_summary": json.dumps(details, ensure_ascii=False),
                "retrieved_at": str(source.get("retrieved_at") or ""),
            })
    for result in state.get("literature_tool_results", []):
        if isinstance(result, dict):
            rows.append({
                "source": "PubMed",
                "status": _source_status(result.get("status")),
                "query_summary": str(result.get("query") or ""),
                "retrieved_at": str(result.get("retrieved_at") or ""),
            })
    return rows


def _investigation_log(report: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    adaptive = _json_object(state.get("adaptive_investigation"))
    synthesis = _json_object(state.get("claim_synthesis"))
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
    draft = report.get("investigation_log")
    draft = draft if isinstance(draft, dict) else {}
    gaps = _deduplicate_strings(
        [item["evidence_gap"] for item in actions if item["evidence_gap"]],
        synthesis.get("evidence_gaps"),
    )
    stop_reason = adaptive.get("stop_reason") or draft.get("stop_reason")
    if not stop_reason:
        stop_reason = (
            "Adaptive follow-up audit completed."
            if actions else "No adaptive follow-up was executed."
        )
    return {
        "identified_evidence_gaps": gaps,
        "planned_actions": [dict(item, status="planned") for item in actions],
        "executed_actions": actions,
        "query_budget": MAX_ADAPTIVE_QUERIES,
        "queries_used": sum(item["status"] == "executed" for item in actions),
        "stop_reason": str(stop_reason),
        "remaining_limitations": _deduplicate_strings(
            adaptive.get("remaining_limitations"), synthesis.get("limitations")
        ),
    }


def finalize_report_from_state(
    report: dict[str, Any], state: Mapping[str, Any]
) -> dict[str, Any]:
    """Replace every mechanically derivable report field from session state.

    The model keeps only its initial completeness judgment. Verified claims, source
    audits, and recorded evidence gaps determine all substantive report content.
    """
    report = dict(report)
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
    statistics = normalized.get("statistics")
    report["statistical_signals"] = [
        {
            "statement": f"{field}: {value}",
            "evidence_ids": [f"INPUT-STAT-{index:03d}"],
            "confidence": "unknown",
            "kind": "observation",
        }
        for index, (field, value) in enumerate(
            sorted(statistics.items()) if isinstance(statistics, dict) else [], start=1
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
            "evidence_ids": [f"QC-BL-{index:03d}"],
            "recommended_check": str(item.get("recommended_check") or ""),
        }
        for index, item in enumerate(risks, start=1)
        if isinstance(item, dict)
    ]
    raw_verification = state.get("verification")
    raw_verification = raw_verification if isinstance(raw_verification, dict) else {}
    verification = reconcile_verification_from_state(raw_verification, state)
    report["verified_claims"] = list(verification.get("supported_claims") or [])
    report["contradictions"] = list(verification.get("contradictions") or [])
    report["investigation_log"] = _investigation_log(report, state)
    report["query_provenance"] = _query_provenance(state)
    report["report_version"] = "1.0.1"
    source_failures = [
        f"{source.get('source') or key} query was incomplete ({source.get('status') or source.get('completeness')})."
        for key in (
            "region_annotation", "vep_evidence", "database_evidence",
            "clingen_dosage_evidence", "clinvar_evidence", "dbvar_evidence",
            "dgv_evidence",
        )
        if isinstance((source := baseline.get(key)), dict)
        and (
            source.get("status") in {"error", "unavailable"}
            or source.get("completeness") in {"partial", "failed"}
        )
    ]
    if normalized.get("status") != "valid":
        report["report_status"] = "blocked"
    elif verification.get("publication_allowed") is False or source_failures:
        report["report_status"] = "incomplete"
    else:
        report["report_status"] = "complete"
    report["limitations"] = _deduplicate_strings(
        baseline.get("limitations"),
        _json_object(state.get("claim_synthesis")).get("limitations"),
        verification.get("missing_evidence"),
        verification.get("warnings"),
        source_failures,
    )

    # Only exactly supported, verifier-bound claims enter narrative sections.
    # Partially supported claims remain visible in verified_claims with their notes.
    for section in _VERIFIED_REPORT_SECTIONS:
        report[section] = []
    for claim in verification.get("supported_claims", []):
        section = claim.get("report_section")
        if claim.get("verification_status") != "supported" or section not in report:
            continue
        report[section].append({
            "statement": claim.get("text", ""),
            "evidence_ids": list(claim.get("evidence_ids") or []),
            "confidence": claim.get("confidence", "unknown"),
            "kind": claim.get("claim_type", "observation"),
        })

    synthesis = _json_object(state.get("claim_synthesis"))
    next_step_gaps = _deduplicate_strings(
        synthesis.get("evidence_gaps"), verification.get("missing_evidence")
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

    for group in _REPORT_EVIDENCE_GROUPS:
        items = report.get(group)
        if not isinstance(items, list):
            continue
        cleaned = []
        for item in items:
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
            cleaned.append(item)
        report[group] = cleaned

    report["evidence_catalog"] = [
        _catalog_record(evidence_id, index[evidence_id])
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
