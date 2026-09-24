"""Render a structured SVReport JSON file as review-friendly Markdown."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .schemas import SVReport


def _statements(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        return lines + ["No evidence recorded.", ""]
    for item in items:
        evidence = ", ".join(item.get("evidence_ids", [])) or "none"
        lines.append(
            f"- {item.get('statement', '')} "
            f"(kind: {item.get('kind', 'unknown')}; confidence: "
            f"{item.get('confidence', 'unknown')}; evidence: {evidence})"
        )
    return lines + [""]


_STATUS_LABELS = {
    "found": "Found",
    "not_found": "No record found",
    "not_applicable": "Not applicable",
    "unavailable": "Unavailable",
    "error": "Query failed",
    "not_queried": "Not queried",
}


def render_markdown(report: dict[str, Any]) -> str:
    """Convert a validated report-shaped dictionary to Markdown."""
    sv = report.get("sv_summary", {})
    build_original = sv.get("genome_build_original")
    type_original = sv.get("sv_type_original")
    normalization_notes = []
    if build_original and build_original != sv.get("genome_build"):
        normalization_notes.append(
            f"reference build `{build_original}` → `{sv.get('genome_build')}`"
        )
    if type_original and type_original != sv.get("sv_type"):
        normalization_notes.append(
            f"SV type `{type_original}` → `{sv.get('sv_type')}`"
        )
    if sv.get("sv_subtype"):
        normalization_notes.append(f"subtype `{sv['sv_subtype']}`")
    lines = [
        "# Structural Variant Investigation Report",
        "",
        f"**Status:** {report.get('report_status', 'unknown')}",
        "",
        "## Variant summary",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| SV ID | `{sv.get('sv_id', 'unknown')}` |",
        f"| Reference build | {sv.get('genome_build', '?')} |",
        f"| Position | chr{sv.get('chrom', '?')}:{sv.get('start', '?')}-"
        f"{sv.get('end', '?')} |",
        f"| SV type | {sv.get('sv_type', '?')} |",
        "",
    ]
    if sv.get("coordinate_system"):
        lines.insert(-1, f"| Coordinate system | {sv['coordinate_system']} |")
    if sv.get("length_bp") is not None:
        lines.insert(-1, f"| Length | {sv['length_bp']} bp |")
    uncertainty_status = sv.get("breakpoint_uncertainty_status")
    if uncertainty_status:
        start_ci = sv.get("start_confidence_interval")
        end_ci = sv.get("end_confidence_interval")
        lines.insert(
            -1,
            "| Breakpoint uncertainty | "
            f"{uncertainty_status}; start CI={start_ci or 'not provided'}; "
            f"end CI={end_ci or 'not provided'} |",
        )
    if sv.get("sv_type") == "BND":
        if sv.get("mate_chrom") and sv.get("mate_pos") is not None:
            orientation = ""
            if sv.get("local_orientation") and sv.get("mate_orientation"):
                orientation = (
                    f"; orientation={sv['local_orientation']}/{sv['mate_orientation']}"
                )
            lines += [
                "**BND mate:** "
                f"{sv['mate_chrom']}:{sv['mate_pos']}; "
                f"CI={sv.get('mate_confidence_interval') or 'not provided'}"
                f"{orientation}",
                "",
            ]
        else:
            lines += ["**BND mate:** not provided; first-breakend-only analysis", ""]
    if normalization_notes:
        lines += [f"**Input normalization:** {'; '.join(normalization_notes)}", ""]

    baseline_rows = [
        item for item in report.get("query_provenance", [])
        if item.get("source") != "PubMed"
    ]
    if baseline_rows:
        lines += [
            "## Baseline source checks",
            "",
            "| Database or resource | Result |",
            "|---|---|",
        ]
        lines.extend(
            f"| {item.get('source', 'unknown')} | "
            f"{_STATUS_LABELS.get(item.get('status'), item.get('status', 'unknown'))} |"
            for item in baseline_rows
        )
        lines.append("")

    investigation = report.get("investigation_log", {})
    if investigation:
        lines += ["## Adaptive investigation", ""]
        lines.append(
            f"- Query budget used: {investigation.get('queries_used', 0)}/"
            f"{investigation.get('query_budget', 2)}"
        )
        lines.append(
            f"- Stop reason: {investigation.get('stop_reason', 'not recorded')}"
        )
        for action in investigation.get("executed_actions", []):
            lines.append(
                f"- {action.get('action', 'unknown')} — "
                f"{action.get('status', 'unknown')}: "
                f"{action.get('evidence_gap', '')}"
            )
        lines.append("")
    sections = (
        ("Statistical signals", "statistical_signals"),
        ("Gene and region annotation", "gene_region_annotation"),
        ("Population and variant-database evidence", "population_evidence"),
        ("Clinical evidence and phenotype associations", "clinical_phenotype_evidence"),
        ("Literature evidence", "literature_evidence"),
        ("Possible interpretations", "possible_interpretations"),
    )
    for title, key in sections:
        lines.extend(_statements(title, report.get(key, [])))

    qualified = [
        claim for claim in report.get("verified_claims", [])
        if claim.get("verification_status") == "partially_supported"
    ]
    lines += ["## Qualified findings", ""]
    if qualified:
        for claim in qualified:
            evidence = ", ".join(claim.get("evidence_ids", [])) or "none"
            lines.append(
                f"- {claim.get('text', '')} "
                f"(evidence: {evidence}; qualification: "
                f"{claim.get('notes') or 'partially supported'})"
            )
    else:
        lines.append("No partially supported claims recorded.")
    lines.append("")

    lines += ["## Artifact risks", ""]
    for item in report.get("artifact_risks", []):
        lines.append(
            f"- **{item.get('risk_type')} — {item.get('status')}**: "
            f"{item.get('impact')} Recommended check: {item.get('recommended_check')}"
        )
    if not report.get("artifact_risks"):
        lines.append("No risk assessment recorded.")

    for title, key in (
        ("Contradictions", "contradictions"),
        ("Limitations", "limitations"),
        ("Recommended next steps", "recommended_next_steps"),
    ):
        lines += ["", f"## {title}", ""]
        values = report.get(key, [])
        lines.extend([f"- {value}" for value in values] or ["None recorded."])

    lines += ["", "## Evidence catalog", ""]
    for item in report.get("evidence_catalog", []):
        link = f" — {item.get('source_url')}" if item.get("source_url") else ""
        lines.append(
            f"- **{item.get('evidence_id')}** [{item.get('source')}; "
            f"{item.get('match_type')}]: {item.get('summary')}{link}"
        )
    if not report.get("evidence_catalog"):
        lines.append("No evidence records retained.")

    lines += ["", "## Query provenance", ""]
    for item in report.get("query_provenance", []):
        lines.append(
            f"- {item.get('source')}: {item.get('status')} — "
            f"{item.get('query_summary')}"
        )
    if not report.get("query_provenance"):
        lines.append("No query provenance recorded.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="SVReport JSON file")
    parser.add_argument("-o", "--output", type=Path, help="Markdown output path")
    args = parser.parse_args()
    # The renderer is also a command-line boundary: reject malformed or internally
    # inconsistent reports rather than making them look authoritative in Markdown.
    report = SVReport.model_validate_json(
        args.input.read_text(encoding="utf-8")
    ).model_dump(mode="json")
    rendered = render_markdown(report)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
