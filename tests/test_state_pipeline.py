import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from sv_investigator.config import MAX_PUBMED_RECORDS
from sv_investigator.schemas import SVReport, SynthesisOutput
from sv_investigator.state_pipeline import (
    adaptive_and_store,
    baseline_and_store,
    build_evidence_view,
    literature_and_store,
    finalize_report_from_state,
    normalize_and_store,
    reconcile_verification_from_state,
)


class StatePipelineTest(unittest.TestCase):
    def test_synthesis_drops_ungrounded_fact_without_aborting(self):
        result = SynthesisOutput.model_validate({
            "candidate_claims": [
                {
                    "claim_id": "C1", "text": "A sourced fact.",
                    "claim_type": "database_fact",
                    "report_section": "population_evidence",
                    "evidence_ids": ["GNO-BL-001"],
                },
                {
                    "claim_id": "C2", "text": "An unsourced absence claim.",
                    "claim_type": "observation",
                    "report_section": "population_evidence",
                    "evidence_ids": [],
                },
            ]
        })

        self.assertEqual([claim.claim_id for claim in result.candidate_claims], ["C1"])
        self.assertIn("C2", result.limitations[0])

    def test_evidence_view_indexes_exact_records_and_removes_prompt_duplicates(self):
        record = {"evidence_id": "VEP-BL-001", "gene_symbol": "GENE1"}
        state = {
            "baseline_evidence": {
                "status": "complete",
                "vep_evidence": {
                    "status": "found",
                    "records": [record],
                    "limitations": ["prediction only"],
                },
            },
            "adaptive_tool_results": [],
            "literature_tool_results": [],
        }

        view = build_evidence_view(state)

        self.assertIs(view["records_by_id"]["VEP-BL-001"], record)
        vep_context = view["source_context"]["baseline_evidence"]["vep_evidence"]
        self.assertNotIn("records", vep_context)
        self.assertEqual(vep_context["limitations"], ["prediction only"])
        self.assertEqual(view["record_count"], 1)
        self.assertEqual(view["total_record_count"], 1)
        narrowed = build_evidence_view(state, set())
        self.assertEqual(narrowed["records_by_id"], {})
        self.assertEqual(narrowed["total_record_count"], 1)

    def test_report_catalog_uses_verified_claims_not_writer_sections(self):
        state = {
            "baseline_evidence": {
                "status": "complete",
                "retrieved_at": "2026-01-01T00:00:00Z",
                "vep_evidence": {
                    "status": "found",
                    "records": [{
                        "evidence_id": "VEP-BL-001",
                        "record_id": "ENST1",
                        "gene_symbol": "GENE1",
                        "source_url": "https://example.test/ENST1",
                    }],
                },
            },
            "adaptive_tool_results": [],
            "literature_tool_results": [],
            "claim_synthesis": {"candidate_claims": [{
                "claim_id": "C1", "text": "known", "claim_type": "database_fact",
                "report_section": "gene_region_annotation",
                "evidence_ids": ["VEP-BL-001"],
            }]},
            "verification": {
                "publication_allowed": True,
                "supported_claims": [{
                    "claim_id": "C1", "text": "known", "claim_type": "database_fact",
                    "report_section": "gene_region_annotation",
                    "evidence_ids": ["VEP-BL-001"], "confidence": "high",
                    "verification_status": "supported",
                }],
                "rejected_claims": [],
            },
        }
        report = {
            "gene_region_annotation": [
                {"statement": "known", "evidence_ids": ["VEP-BL-001"]},
                {"statement": "invented", "evidence_ids": ["MADE-UP-001"]},
            ],
            "population_evidence": [
                {"statement": "duplicate", "evidence_ids": ["VEP-BL-001"]},
            ],
            "evidence_catalog": [{"evidence_id": "model-written"}],
            "limitations": [],
        }

        result = finalize_report_from_state(report, state)

        self.assertEqual(
            [item["evidence_id"] for item in result["evidence_catalog"]],
            ["VEP-BL-001"],
        )
        self.assertEqual(len(result["gene_region_annotation"]), 1)
        self.assertEqual(result["gene_region_annotation"][0]["statement"], "known")
        self.assertNotIn("MADE-UP-001", json.dumps(result))

    def test_report_mechanical_fields_are_rebuilt_from_state(self):
        claim = {
            "claim_id": "C001", "text": "VEP observation",
            "claim_type": "database_fact", "evidence_ids": ["VEP-BL-001"],
            "report_section": "gene_region_annotation",
            "confidence": "high", "verification_status": "supported", "notes": "",
        }
        state = {
            "normalized_sv": {
                "status": "valid", "sv_id": "sv1", "genome_build": "GRCh38",
                "chrom": "1", "start": 100, "end": 200, "sv_type": "DEL",
                "coordinate_system": "1-based-inclusive", "length_bp": 101,
                "statistics": {"max_fst": 0.4},
            },
            "baseline_evidence": {
                "status": "complete", "limitations": ["baseline limit"],
                "vep_evidence": {
                    "source": "Ensembl VEP", "status": "found",
                    "records": [{"evidence_id": "VEP-BL-001", "record_id": "ENST1"}],
                },
                "artifact_risk": {"risk_items": [{
                    "risk_type": "repeat_region", "status": "present",
                    "impact": "uncertain breakpoint", "recommended_check": "review",
                }]},
            },
            "adaptive_investigation": json.dumps({
                "stop_reason": "done", "remaining_limitations": ["adaptive limit"],
            }),
            "adaptive_tool_results": [{
                "action": "QUERY_EXONS", "evidence_gap": "exons", "reason": "resolve",
                "expected_information_gain": "architecture", "status": "executed",
                "result_status": "found",
            }],
            "literature_tool_results": [],
            "claim_synthesis": {
                "candidate_claims": [{
                    "claim_id": "C001", "text": "VEP observation",
                    "claim_type": "database_fact",
                    "report_section": "gene_region_annotation",
                    "evidence_ids": ["VEP-BL-001"],
                }],
                "evidence_gaps": ["functional assay"], "limitations": [],
            },
            "verification": {
                "publication_allowed": True, "supported_claims": [claim],
                "contradictions": ["none material"], "missing_evidence": [], "warnings": [],
            },
        }
        draft = {
            "report_status": "complete",
            "sv_summary": {"genome_build": "GRCh37"},
            "investigation_log": {
                "executed_actions": [{"action": "invented", "status": "executed"}] * 3,
                "stop_reason": "invented",
            },
            "gene_region_annotation": [{
                "statement": "known", "evidence_ids": ["VEP-BL-001"],
            }],
        }

        result = finalize_report_from_state(draft, state)
        validated = SVReport.model_validate(result)

        self.assertEqual(validated.sv_summary.start, 100)
        self.assertEqual(validated.investigation_log.queries_used, 1)
        self.assertEqual(validated.investigation_log.stop_reason, "done")
        self.assertEqual(validated.statistical_signals[0].evidence_ids, ["INPUT-STAT-001"])
        self.assertEqual(validated.artifact_risks[0].evidence_ids, ["QC-BL-001"])
        self.assertEqual(validated.verified_claims[0].claim_id, "C001")
        self.assertEqual(validated.gene_region_annotation[0].statement, "VEP observation")
        catalog = {item.evidence_id: item for item in validated.evidence_catalog}
        self.assertEqual(catalog["QC-BL-001"].retrieval_status, "found")
        self.assertEqual(catalog["QC-BL-001"].finding_status, "present")
        self.assertEqual(catalog["QC-BL-001"].evidence_type, "technical_qc")
        self.assertIn("artifact_risks.repeat_region", catalog["QC-BL-001"].used_by)
        self.assertIn("verified_claims.C001", catalog["VEP-BL-001"].used_by)
        self.assertEqual(
            validated.recommended_next_steps,
            ["Resolve evidence gap: functional assay"],
        )

    def test_verifier_cannot_rewrite_claim_or_publish_partial_claim(self):
        state = {
            "claim_synthesis": {
                "candidate_claims": [
                    {
                        "claim_id": "C1", "text": "A partial overlap was found.",
                        "claim_type": "database_fact",
                        "report_section": "population_evidence",
                        "evidence_ids": ["GNO-BL-001"],
                    },
                    {
                        "claim_id": "C2", "text": "A nearby repeat was found.",
                        "claim_type": "database_fact",
                        "report_section": "gene_region_annotation",
                        "evidence_ids": ["ENS-BL-001"],
                    },
                ],
                "evidence_gaps": [], "limitations": [],
            }
        }
        verification = reconcile_verification_from_state({
            "publication_allowed": True,
            "supported_claims": [
                {
                    "claim_id": "C1", "text": "This exact variant is benign.",
                    "claim_type": "inference",
                    "report_section": "possible_interpretations",
                    "evidence_ids": [], "confidence": "high",
                    "verification_status": "supported",
                },
                {
                    "claim_id": "C2", "text": "The deletion overlaps a repeat.",
                    "confidence": "medium",
                    "verification_status": "partially_supported",
                },
            ],
            "rejected_claims": [], "warnings": [],
        }, state)

        self.assertEqual(
            verification["supported_claims"][0]["text"],
            "A partial overlap was found.",
        )
        self.assertEqual(
            verification["supported_claims"][0]["report_section"],
            "population_evidence",
        )

        state.update({
            "normalized_sv": {
                "status": "valid", "genome_build": "GRCh38", "chrom": "1",
                "start": 10, "end": 20, "sv_type": "DEL",
            },
            "baseline_evidence": {
                "status": "complete",
                "database_evidence": {"status": "found", "records": [{
                    "evidence_id": "GNO-BL-001", "variant_id": "gnomAD-SV-1",
                    "chrom": "1", "pos": 11, "end": 20, "type": "DEL",
                    "af": 0.012, "match_type": "partial_overlap",
                }]},
                "region_annotation": {"status": "found", "features": [{
                    "evidence_id": "ENS-BL-001", "description": "repeat",
                }]},
            },
            "adaptive_tool_results": [], "literature_tool_results": [],
            "verification": verification,
        })
        result = finalize_report_from_state({
            "report_status": "complete",
            "population_evidence": [{
                "statement": "Writer says benign", "evidence_ids": ["GNO-BL-001"],
            }],
            "recommended_next_steps": ["No validation required."],
            "limitations": ["Writer says frequency proves clinical safety."],
        }, state)

        self.assertEqual(
            [item["statement"] for item in result["population_evidence"]],
            ["A partial overlap was found."],
        )
        self.assertEqual(result["gene_region_annotation"], [])
        self.assertNotIn("No validation required.", result["recommended_next_steps"])
        self.assertNotIn("Writer says frequency proves clinical safety.", result["limitations"])
        population_record = next(
            item for item in result["evidence_catalog"]
            if item["evidence_id"] == "GNO-BL-001"
        )
        self.assertEqual(population_record["evidence_type"], "population_variant")
        self.assertEqual(population_record["finding_status"], "partial_overlap")
        self.assertEqual(population_record["key_facts"]["af"], 0.012)
        self.assertEqual(population_record["key_facts"]["position"], "1:11-20")

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

    def test_verification_conservatively_qualifies_model_overreach(self):
        candidates = [
            {
                "claim_id": "C1", "text": "This corresponds to the same variant.",
                "claim_type": "database_fact", "report_section": "population_evidence",
                "evidence_ids": ["GNO-BL-001"],
            },
            {
                "claim_id": "C2", "text": "The gene is dosage sensitive.",
                "claim_type": "database_fact", "report_section": "literature_evidence",
                "evidence_ids": ["PMID-123"],
            },
            {
                "claim_id": "C3", "text": "The variant is probably benign.",
                "claim_type": "hypothesis", "report_section": "possible_interpretations",
                "evidence_ids": ["GNO-BL-001"],
            },
            {
                "claim_id": "C4", "text": "The evidence suggests a benign variant.",
                "claim_type": "inference", "report_section": "possible_interpretations",
                "evidence_ids": ["GNO-BL-001"],
            },
        ]
        state = {
            "claim_synthesis": {"candidate_claims": candidates},
            "baseline_evidence": {"database_evidence": {"records": [{
                "evidence_id": "GNO-BL-001", "match_type": "partial_overlap",
            }]}},
            "literature_tool_results": [{"records": [{
                "evidence_id": "PMID-123", "pmid": "123", "title": "A title",
            }]}],
        }
        verdicts = {
            "publication_allowed": True,
            "supported_claims": [
                {
                    "claim_id": claim["claim_id"], "confidence": "high",
                    "verification_status": "supported",
                }
                for claim in candidates
            ],
        }

        result = reconcile_verification_from_state(verdicts, state)

        self.assertEqual(
            [claim["verification_status"] for claim in result["supported_claims"]],
            ["partially_supported"] * 4,
        )
        self.assertEqual(result["supported_claims"][2]["confidence"], "low")
        self.assertEqual(result["supported_claims"][3]["confidence"], "low")
        self.assertEqual(len(result["warnings"]), 4)

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
