from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sv_investigator.runner import (
    Case,
    _case_is_complete,
    _write_summary,
    collect_metrics,
    load_cases,
    parse_final_report,
    run_batch,
)


def valid_report() -> dict:
    return {
        "report_status": "incomplete",
        "sv_summary": {
            "sv_id": "case-1",
            "genome_build": "GRCh38",
            "chrom": "1",
            "start": 100,
            "end": 200,
            "sv_type": "DEL",
        },
        "investigation_log": {
            "query_budget": 2,
            "queries_used": 0,
            "stop_reason": "test fixture",
        },
    }


class RunnerTests(unittest.TestCase):
    def test_load_cases_reads_only_model_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "input.json").write_text('{"sv_id":"visible"}', encoding="utf-8")
            (root / "expected.json").write_text(
                '{"secret":"must-not-leak"}', encoding="utf-8"
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "case_id": "one",
                                "category": "technical",
                                "input": "input.json",
                                "expected": "expected.json",
                                "provenance": "missing-is-not-loaded.json",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            _, cases = load_cases(manifest)

            self.assertEqual(cases[0].input_data, {"sv_id": "visible"})
            self.assertNotIn("secret", json.dumps(cases[0].input_data))

    def test_load_cases_filters_and_rejects_unknown_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.json").write_text("{}", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "case_id": "a",
                                "category": "benchmark",
                                "input": "a.json",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            _, cases = load_cases(manifest, categories=["benchmark"])
            self.assertEqual([case.case_id for case in cases], ["a"])
            with self.assertRaisesRegex(ValueError, "unknown case_id"):
                load_cases(manifest, case_ids=["missing"])

    def test_parse_final_report_accepts_dict_and_exact_json_fence(self) -> None:
        expected = parse_final_report(valid_report())
        fenced = "```json\n" + json.dumps(valid_report()) + "\n```"
        self.assertEqual(parse_final_report(None, fenced), expected)

    def test_parse_final_report_rejects_explanatory_prose(self) -> None:
        with self.assertRaises(json.JSONDecodeError):
            parse_final_report(None, "Here is the report: " + json.dumps(valid_report()))

    def test_collect_metrics_keeps_report_and_run_status_separate(self) -> None:
        case = Case("one", "technical", "", Path("input.json"), {})
        state = {
            "baseline_evidence": {
                "database_evidence": {
                    "status": "found",
                    "records": [{}, {}],
                }
            },
            "adaptive_tool_results": [{"status": "found"}],
        }
        event = SimpleNamespace(
            usage_metadata=SimpleNamespace(
                model_dump=lambda: {"prompt_token_count": 7, "total_token_count": 9}
            )
        )
        metrics = collect_metrics(
            case=case,
            status="complete",
            elapsed_seconds=1.25,
            state=state,
            events=[event],
            report={"report_status": "incomplete"},
            error=None,
        )
        self.assertEqual(metrics["run_status"], "complete")
        self.assertEqual(metrics["report_status"], "incomplete")
        self.assertEqual(metrics["sources"]["gnomad_sv"]["record_count"], 2)
        self.assertEqual(metrics["token_usage"]["total_token_count"], 9)

    def test_summary_and_resume_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            case_dir = run_dir / "cases" / "one"
            case_dir.mkdir(parents=True)
            metrics = {
                "case_id": "one",
                "category": "test",
                "run_status": "complete",
                "schema_valid": True,
            }
            (case_dir / "metrics.json").write_text(
                json.dumps(metrics), encoding="utf-8"
            )
            summary = _write_summary(run_dir, [metrics])
            self.assertTrue(summary["all_complete"])
            self.assertTrue(_case_is_complete(case_dir))
            self.assertTrue((run_dir / "summary.tsv").exists())


class BatchExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_fail_fast_summary_does_not_call_partial_run_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("a", "b"):
                (root / f"{name}.json").write_text("{}", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "corpus_version": "test",
                        "cases": [
                            {"case_id": "a", "input": "a.json"},
                            {"case_id": "b", "input": "b.json"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = SimpleNamespace(
                manifest=manifest,
                case=[],
                category=[],
                list=False,
                run_dir=None,
                output=root / "runs",
                resume=False,
                rerun_completed=False,
                case_timeout=10.0,
                save_events="none",
                fail_fast=True,
            )

            async def fake_execute(case, case_dir, **_kwargs):
                case_dir.mkdir(parents=True, exist_ok=True)
                metrics = {
                    "case_id": case.case_id,
                    "category": case.category,
                    "run_status": "invalid_report",
                    "schema_valid": False,
                }
                (case_dir / "metrics.json").write_text(
                    json.dumps(metrics), encoding="utf-8"
                )
                return metrics

            with patch("sv_investigator.runner.execute_case", new=fake_execute):
                run_dir, summary = await run_batch(args)

            self.assertFalse(summary["all_complete"])
            self.assertTrue(summary["stopped_early"])
            self.assertEqual(summary["total"], 1)
            self.assertEqual(summary["selected_case_count"], 2)
            saved_manifest = json.loads(
                (run_dir / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("expected", json.dumps(saved_manifest))
            self.assertNotIn("provenance", json.dumps(saved_manifest))


if __name__ == "__main__":
    unittest.main()
