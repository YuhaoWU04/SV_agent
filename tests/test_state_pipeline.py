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
    def test_skipped_required_baseline_cannot_publish_a_complete_report(self):
        state = {}
        normalize_and_store(json.dumps({"genome_build": "GRCh38", "chrom": "1",
                                       "start": 10, "end": 20, "sv_type": "DEL"}), state)
        state["verification"] = {"publication_allowed": True}
        report = finalize_report_from_state({}, state)
        self.assertEqual(report["report_status"], "incomplete")
        self.assertIn("Required baseline collection did not finish", " ".join(report["limitations"]))
        SVReport.model_validate(report)

    def test_duplicate_claim_ids_are_rejected_before_unreferenced_claim_filter(self):
        claims = [{"claim_id": "C1", "text": "Fact", "claim_type": "database_fact",
                   "report_section": "gene_region_annotation", "evidence_ids": ids}
                  for ids in ([], ["ENS-BL-001"])]
        with self.assertRaisesRegex(ValueError, "candidate claim IDs must be unique"):
            SynthesisOutput.model_validate({"candidate_claims": claims})

    def test_report_reuses_reconciled_verdict_and_accepts_legacy_json(self):
        state = {"normalized_sv": {"status": "valid", "genome_build": "GRCh38",
                                  "chrom": "1", "start": 10, "end": 20, "sv_type": "DEL"},
                 "verification": {"publication_allowed": True}}
        with patch("sv_investigator.state_pipeline.reconcile_verification_from_state",
                   wraps=reconcile_verification_from_state) as reconcile:
            report = finalize_report_from_state({}, state)
        self.assertEqual(reconcile.call_count, 1)
        self.assertEqual(report["report_status"], "complete")
        state["verification"] = json.dumps(state["verification"])
        self.assertEqual(finalize_report_from_state({}, state), report)
        SVReport.model_validate(report)

    def test_incomplete_queries_in_each_stage_are_reported_without_discarding_results(self):
        source = {"source": "Test database", "status": "error", "completeness": "failed",
                  "query_region": [10, 20]}
        fixtures = [
            ("baseline", {"baseline_evidence": {"database_evidence": source}}),
            ("adaptive", {"adaptive_tool_results": [{"status": "executed", "action": "QUERY_EXONS",
                           "result": {"status": "executed", "result": source}}]}),
            ("adaptive", {"adaptive_tool_results": [{"status": "executed", "action": "QUERY_EXONS",
                           "result": {"status": "executed", "result": {"source": "Ensembl",
                            "completeness": "partial", "results": [{"status": "found",
                             "truncated": True, "role": "nominal", "query_region": "1:10-20"}]}}}]}),
            ("literature", {"literature_tool_results": [source]}),
            ("literature", {"literature_tool_results": [{"source": "PubMed", "status": "found",
                             "completeness": "partial", "query": "GENE", "records": [
                                 {"pmid": "1", "title": "Study", "abstract_status": "error"}]}]}),
        ]
        for stage, evidence in fixtures:
            with self.subTest(stage=stage, evidence=evidence):
                state = {"normalized_sv": {"status": "valid", "genome_build": "GRCh38",
                          "chrom": "1", "start": 10, "end": 20, "sv_type": "DEL"},
                         "verification": {"publication_allowed": True}, **evidence}
                report = finalize_report_from_state({}, state)
                self.assertEqual(report["report_status"], "incomplete")
                self.assertEqual(report["query_provenance"][0]["stage"], stage)
                self.assertTrue(any(f"{stage} query was incomplete" in item for item in report["limitations"]))
                SVReport.model_validate(report)
        state["literature_tool_results"] = [{"source": "PubMed", "status": "not_found",
                                             "query": "GENE", "records": []}]
        self.assertEqual(finalize_report_from_state({}, state)["report_status"], "complete")

    def test_all_retained_hypotheses_are_low_without_promoting_rejections(self):
        candidate = {"claim_id": "H", "text": "The intronic deletion may alter splicing.",
                     "claim_type": "hypothesis", "report_section": "possible_interpretations",
                     "evidence_ids": ["INPUT-STAT-001"]}
        for status in ("supported", "partially_supported", "unsupported", "conflicting"):
            with self.subTest(status=status):
                state = {"normalized_sv": {"statistics": {"fst": 0.39}},
                         "claim_synthesis": {"candidate_claims": [candidate]}}
                verification = {"publication_allowed": True,
                    "supported_claims" if status in {"supported", "partially_supported"} else "rejected_claims": [{
                        "claim_id": "H", "verification_status": status,
                        "confidence": "medium", "notes": "The splicing link is untested.",
                    }]}
                result = reconcile_verification_from_state(verification, state)
                if status in {"supported", "partially_supported"}:
                    claim = result["supported_claims"][0]
                    self.assertEqual(claim["confidence"], "low")
                    self.assertEqual(claim["verification_status"], "partially_supported")
                    self.assertEqual(claim["text"], candidate["text"])
                    self.assertIn("untested", claim["notes"])
                    self.assertEqual(reconcile_verification_from_state(result, state), result)
                else:
                    self.assertEqual(result["supported_claims"], [])
                    self.assertEqual(result["rejected_claims"][0]["verification_status"], status)

    def test_abstract_survives_state_lookup_and_report_catalog(self):
        from sv_investigator.state_pipeline import prepare_verification_evidence, query_verification_evidence
        abstract = "The study reports an association between GENE1 and trait X."
        state = {"literature_tool_results": [{"status": "found", "records": [{
            "evidence_id": "PMID-123", "pmid": "123", "title": "Study A",
            "abstract_status": "found", "abstract": abstract,
            "abstract_source_url": "https://example.org/abstract/123",
        }]}], "claim_synthesis": {"candidate_claims": [{
            "claim_id": "L", "text": "The abstract reports an association between GENE1 and trait X.",
            "claim_type": "database_fact", "report_section": "literature_evidence",
            "evidence_ids": ["PMID-123"],
        }]}, "verification": {"publication_allowed": True, "supported_claims": [{
            "claim_id": "L", "confidence": "high", "verification_status": "supported",
        }]}}
        prepare_verification_evidence(state)
        self.assertEqual(state["evidence_view"]["records_by_id"]["PMID-123"]["abstract"], abstract)
        fetched = query_verification_evidence(state, evidence_ids=["PMID-123"])
        self.assertEqual(fetched["records_by_id"]["PMID-123"]["record"]["abstract"], abstract)
        report = finalize_report_from_state({}, state)
        self.assertEqual(report["evidence_catalog"][0]["evidence_type"], "literature_abstract")
        self.assertEqual(report["evidence_catalog"][0]["key_facts"]["abstract"], abstract)
        self.assertEqual(report["literature_evidence"][0]["confidence"], "high")

    def test_rejected_claim_cannot_return_as_a_qualified_finding(self):
        from sv_investigator.render_report import render_markdown

        text = "L1MC5, dust, AT_rich, and AluSz overlap the start confidence interval."
        for status in ("supported", "partially_supported"):
            with self.subTest(status=status):
                state = {
                    "claim_synthesis": {"candidate_claims": [{
                        "claim_id": "C16", "text": text,
                        "claim_type": "database_fact",
                        "report_section": "gene_region_annotation",
                        "evidence_ids": ["ENS-BL-START-REPEAT-001"],
                    }]},
                    "verification": {
                        "publication_allowed": True,
                        "rejected_claims": [{
                            "claim_id": "C16", "verification_status": status,
                            "confidence": "medium", "notes": "Only L1MC5 overlaps this interval.",
                        }],
                    },
                }
                original = json.dumps(state, sort_keys=True)
                verification = reconcile_verification_from_state(state["verification"], state)
                self.assertEqual(verification["supported_claims"], [])
                rejected = verification["rejected_claims"][0]
                self.assertEqual(rejected["text"], text)
                self.assertEqual(rejected["verification_status"], "unsupported")
                self.assertIn("Only L1MC5", rejected["notes"])
                self.assertIn(status, rejected["notes"])
                self.assertTrue(any("C16" in warning for warning in verification["warnings"]))
                self.assertEqual(reconcile_verification_from_state(verification, state), verification)
                report = finalize_report_from_state({}, state)
                self.assertEqual(report["verified_claims"], [])
                self.assertEqual(report["gene_region_annotation"], [])
                self.assertNotIn(text, render_markdown(report))
                self.assertEqual(json.dumps(state, sort_keys=True), original)

    def test_rejected_verdict_takes_precedence_over_duplicate_support(self):
        state = {"claim_synthesis": {"candidate_claims": [{
            "claim_id": "C16", "text": "An inaccurate finding.",
            "claim_type": "database_fact", "evidence_ids": [],
        }]}}
        result = reconcile_verification_from_state({
            "supported_claims": [{"claim_id": "C16", "verification_status": "supported"}],
            "rejected_claims": [{
                "claim_id": "C16", "verification_status": "conflicting",
                "notes": "Coordinates contradict the finding.",
            }],
        }, state)
        self.assertEqual(result["supported_claims"], [])
        self.assertEqual(result["rejected_claims"][0]["verification_status"], "conflicting")
        self.assertIn("Coordinates contradict", result["rejected_claims"][0]["notes"])

    def test_metadata_claim_can_enter_literature_but_overreach_cannot(self):
        cases = [
            ("TITLE", "The paper title reports an association between X and Y.", "supported"),
            ("MECHANISM", "This SV causes Y by disrupting X.", "unsupported"),
            ("PARTIAL", "The paper reports X.", "partially_supported"),
        ]
        state = {"literature_tool_results": [{"records": [{
                    "evidence_id": "PMID-123", "pmid": "123", "title": "Association between X and Y"}]}],
                 "claim_synthesis": {"candidate_claims": [
                     {"claim_id": cid, "text": text, "claim_type": "database_fact",
                      "report_section": "literature_evidence", "evidence_ids": ["PMID-123"]}
                     for cid, text, status in cases]},
                 "verification": {"publication_allowed": True, "supported_claims": [
                     {"claim_id": cid, "verification_status": status, "confidence": "high",
                      "notes": "Title metadata only; no SV-specific experiment was retrieved."}
                     for cid, text, status in cases]}}
        report = finalize_report_from_state({}, state)
        self.assertEqual([s["statement"] for s in report["literature_evidence"]], [cases[0][1]])
        self.assertEqual(report["literature_evidence"][0]["confidence"], "high")
        self.assertEqual(report["literature_evidence"][0]["verification_status"], "supported")
        self.assertFalse(any("Only PubMed citation metadata" in warning for warning in report["limitations"]))
        self.assertEqual([c["claim_id"] for c in report["verified_claims"]], ["TITLE", "PARTIAL"])
        from sv_investigator.render_report import render_markdown
        markdown = render_markdown(report)
        self.assertNotIn(cases[2][1], markdown)
        self.assertIn("`verified_claims` for review: PARTIAL.", markdown)

    def test_qualified_interpretations_are_visible_without_promoting_facts(self):
        from sv_investigator.render_report import render_markdown
        cases = [
            ("H", "hypothesis", "possible_interpretations", "supported", "Candidate mechanism; not demonstrated."),
            ("I", "inference", "possible_interpretations", "partially_supported", "No direct functional evidence."),
            ("F", "database_fact", "population_evidence", "partially_supported", "Only partial evidence."),
            ("U", "hypothesis", "possible_interpretations", "unsupported", "No basis."),
            ("C", "inference", "possible_interpretations", "conflicting", "Conflicting evidence."),
            ("N", "inference", "possible_interpretations", "partially_supported", ""),
        ]
        state = {"normalized_sv": {"statistics": {"fst": 0.3}},
                 "claim_synthesis": {"candidate_claims": [
                     {"claim_id": cid, "text": cid, "claim_type": kind,
                      "report_section": section, "evidence_ids": ["INPUT-STAT-001"]}
                     for cid, kind, section, status, notes in cases]},
                 "verification": {"publication_allowed": True, "supported_claims": [
                     {"claim_id": cid, "verification_status": status,
                      "confidence": "high", "notes": notes}
                     for cid, kind, section, status, notes in cases]}}
        report = finalize_report_from_state({}, state)
        self.assertEqual([s["statement"] for s in report["possible_interpretations"]], ["H", "I"])
        self.assertEqual(report["population_evidence"], [])
        hypothesis = report["possible_interpretations"][0]
        self.assertEqual(hypothesis["kind"], "hypothesis")
        self.assertEqual(hypothesis["confidence"], "low")
        self.assertEqual(hypothesis["verification_status"], "partially_supported")
        validated = SVReport.model_validate(report).model_dump(mode="json")
        self.assertIn("Qualification (partially_supported)", render_markdown(validated))
        self.assertNotIn("## Qualified findings", render_markdown(validated))
        self.assertEqual(
            [claim["claim_id"] for claim in validated["verified_claims"]
             if claim["verification_status"] == "partially_supported"],
            ["H", "I", "F", "N"],
        )
        self.assertIn("A hypothesis is not an established finding.", hypothesis["qualification"])

    def test_input_fact_type_and_call_rate_signals_survive_finalization(self):
        from sv_investigator.tools import assess_artifact_risk
        from sv_investigator.render_report import render_markdown
        normalized = {"quality": {"call_rate_A": 1.0, "call_rate_B": 1.0},
                      "statistics": {"fst_max": 0.3474}}
        state = {"normalized_sv": normalized,
                 "baseline_evidence": {"artifact_risk": assess_artifact_risk(json.dumps(normalized))},
                 "claim_synthesis": {"candidate_claims": [{
                     "claim_id": "C1", "text": "Input Fst is 0.3474.",
                     "claim_type": "database_fact", "report_section": "population_evidence",
                     "evidence_ids": ["INPUT-STAT-001"]}]},
                 "verification": {"supported_claims": [{"claim_id": "C1",
                     "verification_status": "supported", "confidence": "high"}]}}
        report = finalize_report_from_state({}, state)
        self.assertEqual(report["verified_claims"][0]["claim_type"], "observation")
        self.assertEqual(report["population_evidence"][0]["kind"], "observation")
        self.assertFalse({"low_call_rate", "genotype_missingness"} & {r["risk_type"] for r in report["artifact_risks"]})
        self.assertIn("call_rate_A: 1.0", render_markdown(report))
        records = build_evidence_view(state)["records_by_id"]
        for signal in report["statistical_signals"]:
            record = records[signal["evidence_ids"][0]]
            self.assertEqual(signal["statement"], f"{record['field']}: {record['value']}")
            self.assertEqual(signal["kind"], "observation")
        self.assertEqual(len(report["statistical_signals"]), 3)
        self.assertNotIn("INPUT-CALL-RATES", records)
        self.assertTrue(any(r["key_facts"].get("field") == "call_rate_A" for r in report["evidence_catalog"]))

    def test_report_model_comes_from_runtime_config(self):
        with patch("sv_investigator.state_pipeline.MODEL", "test-runtime-model"):
            report = finalize_report_from_state({"model": "model-written-value"}, {})
        self.assertEqual(report["model"], "test-runtime-model")
        from sv_investigator.render_report import render_markdown
        validated = SVReport.model_validate(report).model_dump(mode="json")
        self.assertIn("**Model:** test-runtime-model", render_markdown(validated))
        validated.pop("model")
        self.assertIn("**Model:** Not recorded", render_markdown(validated))

    def test_call_rates_and_statistical_context_reach_evidence_view(self):
        state = {"normalized_sv": {
            "quality": {"call_rate_A": 1.0, "call_rate_B": 0.9},
            "statistical_context": "Labels shuffled 1000 times.",
        }}
        records = build_evidence_view(state)["records_by_id"]
        self.assertEqual(records["INPUT-STAT-001"]["field"], "call_rate_A")
        self.assertEqual(records["INPUT-STAT-001"]["value"], 1.0)
        self.assertEqual(records["INPUT-STAT-002"]["field"], "call_rate_B")
        self.assertEqual(records["INPUT-STAT-002"]["value"], 0.9)
        self.assertEqual(records["INPUT-STAT-CONTEXT"]["summary"], "Labels shuffled 1000 times.")
        report = finalize_report_from_state({}, state)
        self.assertEqual(report["statistical_context"], "Labels shuffled 1000 times.")
        from sv_investigator.render_report import render_markdown
        validated = SVReport.model_validate(report).model_dump(mode="json")
        self.assertIn("## Statistical context\n\nLabels shuffled 1000 times.", render_markdown(validated))

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
                "approved_evidence_gaps": ["functional assay"],
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
        self.assertEqual(validated.investigation_log.stop_reason,
                         "Recorded adaptive follow-ups finished. No further follow-up was executed.")
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

    def test_query_facts_and_reviewed_text_cannot_be_replaced_by_model_prose(self):
        from sv_investigator.render_report import render_markdown
        hypothesis = "The intronic deletion may affect splicing."
        gap = "Test the deletion for a splicing effect."
        bad_gap = "The exon lookup failed; alternative exons remain unresolved."
        limitation = "The retrieved titles do not establish an SV effect."
        state = {
            "normalized_sv": {"status": "valid", "genome_build": "GRCh38", "sv_type": "DEL",
                              "chrom": "1", "start": 100, "end": 200, "statistics": {"fst": 0.39}},
            "baseline_evidence": {"dbvar_evidence": {
                "source": "NCBI dbVar", "status": "found", "completeness": "complete",
                "query_regions": [{"interval": [100, 200]}],
                "search_counts": [{"total_count": 74, "search_truncated": True}],
                "search_uid_count": 50, "returned_record_count": 10,
                "records_truncated": True,
            }},
            "adaptive_tool_results": [{
                "action": "QUERY_EXONS", "status": "executed", "result_status": "not_found",
                "evidence_gap": "Original planning premise, not a finding.",
                "result": {"result": {"source": "Ensembl", "results": [{
                    "status": "not_found", "query_region": "1:100-200", "feature": "exon",
                    "records": [], "error": None, "truncated": False,
                }]}},
            }],
            "adaptive_investigation": {"stop_reason": "All transcripts are unaffected.",
                                       "remaining_limitations": ["Unreviewed adaptive assertion."]},
            "claim_synthesis": {
                "candidate_claims": [{"claim_id": "H", "text": hypothesis,
                    "claim_type": "hypothesis", "report_section": "possible_interpretations",
                    "evidence_ids": ["INPUT-STAT-001"]}],
                "evidence_gaps": [gap, bad_gap],
                "limitations": [limitation, "No functional research exists."],
            },
            "verification": {
                "publication_allowed": True,
                "supported_claims": [{"claim_id": "H", "text": "The SV causes disease.",
                    "verification_status": "supported", "confidence": "high",
                    "notes": "Intronic location motivates testing; the splicing effect is untested."}],
                "approved_evidence_gaps": [gap, "A rewritten gap."],
                "approved_limitations": [limitation, "A new limitation."],
            },
        }
        view = build_evidence_view(state)
        self.assertEqual(view["source_context"]["baseline_evidence"]["dbvar_evidence"]["query_regions"],
                         [{"interval": [100, 200]}])
        report = SVReport.model_validate(finalize_report_from_state({}, state)).model_dump(mode="json")
        rendered = render_markdown(report)
        self.assertEqual(report["recommended_next_steps"], ["Resolve evidence gap: " + gap])
        self.assertEqual(report["investigation_log"]["remaining_limitations"], [limitation])
        self.assertEqual(report["possible_interpretations"][0]["statement"], hypothesis)
        self.assertEqual(report["possible_interpretations"][0]["confidence"], "low")
        for forbidden in (bad_gap, "No functional research exists.", "A rewritten gap.",
                          "A new limitation.", "All transcripts are unaffected.",
                          "Original planning premise", "Unreviewed adaptive assertion.", "The SV causes disease."):
            self.assertNotIn(forbidden, rendered)
        self.assertIn("Untested hypothesis:", rendered)
        self.assertIn("No matching records were returned within the reported query scope.", rendered)
        self.assertIn("1:100-200", rendered)
        self.assertIn("returned_record_count=0", rendered)
        self.assertIn("search_hit_count_across_queries=74", rendered)
        self.assertIn("search_uid_count=50", rendered)
        self.assertIn("returned_record_count=10", rendered)
        self.assertIn("Yes. Returned records are not exhaustive.", rendered)
        # Legacy verdicts have no approval lists: do not silently publish their draft prose.
        state["verification"].pop("approved_evidence_gaps")
        state["verification"].pop("approved_limitations")
        legacy = finalize_report_from_state({}, state)
        self.assertNotIn(limitation, legacy["limitations"])
        self.assertFalse(any(gap in item for item in legacy["recommended_next_steps"]))

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
                "claim_id": "C2", "text": "The retrieved publication is titled 'A title'.",
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
            ["partially_supported", "supported", "partially_supported", "partially_supported"],
        )
        self.assertEqual(result["supported_claims"][2]["confidence"], "low")
        self.assertEqual(result["supported_claims"][3]["confidence"], "low")
        self.assertEqual(result["supported_claims"][1]["confidence"], "high")
        self.assertEqual(len(result["warnings"]), 3)

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
