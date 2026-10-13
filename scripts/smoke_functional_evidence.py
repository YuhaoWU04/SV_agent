"""Live read-only adapter checks; no agents or paid model calls."""
import argparse
import json
from pathlib import Path

from sv_investigator.tools import (
    normalize_sv_input, query_functional_track, query_qtl_context, assess_artifact_risk,
    _add_evidence_ids,
)
from sv_investigator.state_pipeline import build_evidence_view


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for path in args.inputs:
        sv = normalize_sv_input(path.read_text(encoding="utf-8"))
        assert sv["status"] == "valid", sv
        raw = json.dumps(sv)
        evidence = {}
        for key, prefix, query, query_args in (
            ("regulatory_element_evidence", "CCRE", query_functional_track, ("ccre",)),
            ("regulatory_gene_link_evidence", "REG", query_functional_track, ("links",)),
            ("qtl_evidence", "QTL", query_qtl_context, ()),
            ("mappability_evidence", "MAP", query_functional_track, ("map",)),
        ):
            result = _add_evidence_ids(query(raw, *query_args), f"{prefix}-BL")
            evidence[key] = result
            print(path.stem, key, result["status"], result.get("completeness"),
                  len(result["records"]), flush=True)
        evidence["artifact_risk"] = assess_artifact_risk(
            raw, mappability_json=json.dumps(evidence["mappability_evidence"]))
        state = {"normalized_sv": sv, "baseline_evidence": evidence}
        state["evidence_view"] = build_evidence_view(state)
        (args.output / f"{path.stem}.json").write_text(
            json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
