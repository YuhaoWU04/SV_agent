"""Render a structured SVReport JSON file as review-friendly Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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
        f"**SV:** {sv.get('sv_id', 'unknown')} — {sv.get('genome_build', '?')} "
        f"{sv.get('chrom', '?')}:{sv.get('start', '?')}-{sv.get('end', '?')} "
        f"{sv.get('sv_type', '?')}",
        "",
    ]
    if sv.get("coordinate_system"):
        lines += [f"**Coordinate system:** {sv['coordinate_system']}", ""]
    uncertainty_status = sv.get("breakpoint_uncertainty_status")
    if uncertainty_status:
        start_ci = sv.get("start_confidence_interval")
        end_ci = sv.get("end_confidence_interval")
        lines += [
            "**Breakpoint uncertainty:** "
            f"{uncertainty_status}; start CI={start_ci or 'not provided'}; "
            f"end CI={end_ci or 'not provided'}",
            "",
        ]
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
    if sv.get("length_bp") is not None:
        lines += [f"**SV length:** {sv['length_bp']} bp", ""]
    if normalization_notes:
        lines += [f"**Input normalization:** {'; '.join(normalization_notes)}", ""]
    sections = (
        ("Statistical signals", "statistical_signals"),
        ("Gene and region annotation", "gene_region_annotation"),
        ("Population evidence", "population_evidence"),
        ("Clinical and phenotype evidence", "clinical_phenotype_evidence"),
        ("Literature evidence", "literature_evidence"),
        ("Functional evidence", "functional_evidence"),
        ("Possible interpretations", "possible_interpretations"),
    )
    for title, key in sections:
        lines.extend(_statements(title, report.get(key, [])))

    lines += ["## Artifact risks", ""]
    for item in report.get("artifact_risks", []):
        lines.append(f"- **{item.get('risk_type')} — {item.get('status')}**: {item.get('impact')} Recommended check: {item.get('recommended_check')}")
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
        lines.append(f"- {item.get('source')}: {item.get('status')} — {item.get('query_summary')}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="SVReport JSON file")
    parser.add_argument("-o", "--output", type=Path, help="Markdown output path")
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    rendered = render_markdown(report)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
