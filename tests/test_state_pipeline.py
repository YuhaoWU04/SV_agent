import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from sv_investigator.config import MAX_PUBMED_RECORDS
from sv_investigator.state_pipeline import (
    adaptive_and_store,
    baseline_and_store,
    literature_and_store,
    normalize_and_store,
)


class StatePipelineTest(unittest.TestCase):
    def test_normalizer_writes_raw_result_and_resets_per_run_evidence(self):
        state = {"adaptive_tool_results": [{"stale": True}]}
        result = normalize_and_store(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }), state)
        self.assertIs(state["normalized_sv"], result)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(state["adaptive_tool_results"], [])
        self.assertEqual(state["literature_tool_results"], [])

    @patch("sv_investigator.state_pipeline.collect_baseline_evidence")
    def test_baseline_stores_tool_result_without_rewriting(self, collect):
        state = {}
        normalize_and_store(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }), state)
        raw = {"status": "complete", "database_evidence": {
            "records": [{"evidence_id": "GNO-BL-001", "af": 0.125}],
        }}
        collect.return_value = raw
        self.assertIs(baseline_and_store(state), raw)
        self.assertIs(state["baseline_evidence"], raw)
        passed_candidate = json.loads(collect.call_args.args[0])
        self.assertEqual(passed_candidate, state["normalized_sv"])

    @patch("sv_investigator.state_pipeline.collect_baseline_evidence")
    def test_invalid_input_blocks_baseline_without_query(self, collect):
        state = {}
        normalize_and_store('{"sv_type": "DEL"}', state)
        result = baseline_and_store(state)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(state["baseline_evidence"], result)
        collect.assert_not_called()

    @patch("sv_investigator.state_pipeline.run_budgeted_adaptive_action")
    def test_adaptive_preserves_full_success_and_failure(self, run):
        state = {}
        normalize_and_store(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }), state)
        raw = {"status": "executed", "result": {"status": "error", "error": "TimeoutError"}}
        run.return_value = raw
        result = adaptive_and_store("QUERY_EXONS", "exon status", "resolve gap", "exons", state)
        self.assertIs(result, raw)
        self.assertIs(state["adaptive_tool_results"][0], raw)
        self.assertEqual(json.loads(run.call_args.kwargs["normalized_sv_json"]),
                         state["normalized_sv"])

    @patch("sv_investigator.state_pipeline.search_pubmed")
    def test_literature_preserves_metadata_and_stable_id(self, search):
        state = {}
        normalize_and_store(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }), state)
        raw = {"status": "found", "records": [{"pmid": "123", "title": "Example"}]}
        search.return_value = raw
        self.assertIs(literature_and_store("test", 5, state), raw)
        self.assertIs(state["literature_tool_results"][0], raw)
        self.assertEqual(raw["records"][0]["evidence_id"], "PMID-123")
        self.assertEqual(raw["queries_used"], 1)

    @patch("sv_investigator.state_pipeline.search_pubmed")
    def test_literature_enforces_query_budget_and_deduplicates(self, search):
        state = {}
        normalize_and_store(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }), state)
        search.side_effect = [
            {"status": "found", "records": [{"pmid": "1"}, {"pmid": "2"}]},
            {"status": "found", "records": [{"pmid": "2"}, {"pmid": "3"}]},
            {"status": "not_found", "records": []},
        ]
        first = literature_and_store("  Gene   AND DEL ", 99, state)
        duplicate = literature_and_store("gene and del", 99, state)
        second = literature_and_store("other", 99, state)
        third = literature_and_store("third", 99, state)
        exhausted = literature_and_store("fourth", 99, state)
        self.assertEqual(duplicate["reason"], "duplicate_query")
        self.assertEqual(exhausted["reason"], "query_budget_exhausted")
        self.assertEqual(search.call_count, 3)
        self.assertEqual(
            [call.args[1] for call in search.call_args_list],
            [MAX_PUBMED_RECORDS] * 3,
        )
        self.assertEqual(first["returned_record_count"], 2)
        self.assertEqual(second["duplicate_pmids_excluded"], 1)
        self.assertEqual([row["pmid"] for row in second["records"]], ["3"])
        self.assertEqual(third["queries_remaining"], 0)
        self.assertEqual(len(state["literature_tool_results"]), 3)

    @patch("sv_investigator.state_pipeline.search_pubmed")
    def test_literature_invalid_input_does_not_search(self, search):
        state = {}
        normalize_and_store('{"sv_type": "DEL"}', state)
        result = literature_and_store("test", 5, state)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(state["literature_tool_results"], [])
        search.assert_not_called()

    @patch("sv_investigator.state_pipeline.search_pubmed")
    def test_literature_failed_search_still_consumes_budget(self, search):
        state = {}
        normalize_and_store(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }), state)
        search.return_value = {"source": "PubMed", "status": "error", "error": "TimeoutError"}
        result = literature_and_store("test", 5, state)
        self.assertEqual(result["queries_used"], 1)
        self.assertEqual(result["queries_remaining"], 2)
        self.assertEqual(len(state["literature_tool_results"]), 1)

    @patch("sv_investigator.state_pipeline.search_pubmed")
    def test_literature_budget_and_pmid_dedup_are_atomic(self, search):
        started = Barrier(3)

        def complete_search(query, max_records):
            del query, max_records
            started.wait(timeout=2)
            return {"status": "found", "records": [{"pmid": "123"}]}

        search.side_effect = complete_search
        state = {}
        normalize_and_store(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }), state)

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(
                lambda query: literature_and_store(query, 5, state),
                ["query one", "query two", "query three", "query four"],
            ))

        self.assertEqual(search.call_count, 3)
        self.assertEqual(len(state["literature_query_keys"]), 3)
        self.assertEqual(
            sum(len(item.get("records", [])) for item in state["literature_tool_results"]),
            1,
        )
        self.assertEqual(
            sum(result["status"] == "rejected" for result in results), 1
        )


if __name__ == "__main__":
    unittest.main()
