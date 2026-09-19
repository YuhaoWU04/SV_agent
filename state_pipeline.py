"""Store tool-produced evidence in ADK session state without LLM transcription."""

from __future__ import annotations

import json
import re
import threading
from typing import Any, MutableMapping

from .config import MAX_PUBMED_QUERIES, MAX_PUBMED_RECORDS
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
