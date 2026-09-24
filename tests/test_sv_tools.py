import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from sv_investigator.config import ENSEMBL_HTTP_TIMEOUT_SECONDS
from sv_investigator.render_report import render_markdown
from sv_investigator.schemas import SVReport
from sv_investigator.tools import (
    _ensembl_json_request,
    assess_artifact_risk,
    collect_baseline_evidence,
    execute_adaptive_action,
    normalize_sv_input,
    query_clingen_dosage,
    query_clinvar,
    query_dbvar,
    query_dgv,
    query_ensembl_region,
    query_ensembl_vep,
    query_gnomad_sv,
    run_budgeted_adaptive_action,
    search_pubmed,
)


class SVToolsTest(unittest.TestCase):
    @patch("sv_investigator.tools.execute_adaptive_action")
    def test_adaptive_budget_is_atomic_for_parallel_calls(self, execute):
        started = Barrier(2)

        def complete_action(normalized_sv_json, action):
            del normalized_sv_json
            started.wait(timeout=2)
            return {
                "status": "executed", "action": action,
                "result": {"status": "not_found"},
            }

        execute.side_effect = complete_action
        state = {
            "temp:adaptive_action_history": [],
            "temp:adaptive_query_count": 0,
        }
        actions = [
            "QUERY_EXONS", "QUERY_TRANSCRIPTS", "QUERY_NEAREST_GENE_10KB"
        ]

        def run(action):
            return run_budgeted_adaptive_action(
                "{}", action, "gap", "reason", "gain", state
            )

        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(run, actions))

        self.assertEqual(execute.call_count, 2)
        self.assertEqual(state["temp:adaptive_query_count"], 2)
        self.assertEqual(
            sorted(result["status"] for result in results),
            ["executed", "executed", "rejected"],
        )

    @patch("sv_investigator.tools.time.sleep")
    @patch("sv_investigator.tools._json_request")
    def test_ensembl_retries_transient_error(self, request, sleep):
        request.side_effect = [(None, "TimeoutError"), ([{"id": "ENSG1"}], None)]
        payload, error, attempts = _ensembl_json_request(
            "https://rest.ensembl.org/overlap/region/human/1:10-20",
            {"feature": "gene"},
        )
        self.assertEqual(payload, [{"id": "ENSG1"}])
        self.assertIsNone(error)
        self.assertEqual(attempts, 2)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(
            request.call_args.kwargs["timeout_seconds"], ENSEMBL_HTTP_TIMEOUT_SECONDS
        )
        sleep.assert_called_once()

    @patch("sv_investigator.tools.time.sleep")
    @patch("sv_investigator.tools._json_request")
    def test_ensembl_does_not_retry_client_error(self, request, sleep):
        request.return_value = (None, "HTTP 400")
        payload, error, attempts = _ensembl_json_request("https://example.org", {"feature": "gene"})
        self.assertIsNone(payload)
        self.assertEqual(error, "HTTP 400")
        self.assertEqual(attempts, 1)
        request.assert_called_once()
        sleep.assert_not_called()

    @patch("sv_investigator.tools.time.sleep")
    @patch("sv_investigator.tools._json_request")
    def test_ensembl_exhausted_retry_preserves_error(self, request, sleep):
        request.return_value = (None, "HTTP 503")
        payload, error, attempts = _ensembl_json_request("https://example.org", {"feature": "gene"})
        self.assertIsNone(payload)
        self.assertEqual(error, "HTTP 503")
        self.assertEqual(attempts, 2)
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once()

    def test_normalize_valid_sv(self):
        result = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38",
            "chrom": "chr2",
            "start": 100,
            "end": 199,
            "sv_type": "del",
            "statistics": {"fst": 0.2},
        }))
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["chrom"], "2")
        self.assertEqual(result["sv_type"], "DEL")
        self.assertEqual(result["length_bp"], 100)
        self.assertEqual(result["coordinate_system"], "1-based-inclusive")
        self.assertIn("quality_not_provided", result["warnings"])

    def test_normalize_build_aliases_case_insensitively(self):
        aliases = {
            "hg38": "GRCh38",
            "HG38": "GRCh38",
            "grch38.p14": "GRCh38",
            "build-38": "GRCh38",
            "hg19": "GRCh37",
            "HG19": "GRCh37",
            "GRCh37.p13": "GRCh37",
            "b37": "GRCh37",
        }
        for alias, expected in aliases.items():
            with self.subTest(alias=alias):
                result = normalize_sv_input(json.dumps({
                    "genome_build": alias, "chrom": "chrM", "start": 1,
                    "end": 1, "sv_type": "DEL",
                }))
                self.assertEqual(result["status"], "valid")
                self.assertEqual(result["genome_build"], expected)
                self.assertEqual(result["genome_build_original"], alias)
                self.assertEqual(result["chrom"], "MT")

    def test_normalize_mobile_element_sv_types(self):
        aliases = {
            "ALU": ("INS", "ALU"),
            "line": ("INS", "LINE1"),
            "LINE-1 insertion": ("INS", "LINE1"),
            "L1": ("INS", "LINE1"),
            "L1 insertion": ("INS", "LINE1"),
            "SVA": ("INS", "SVA"),
            "MEI": ("INS", "MEI"),
            "<INS:ME:ALU>": ("INS", "ALU"),
            "deletion": ("DEL", None),
            "gain": ("DUP", None),
            "translocation": ("BND", None),
        }
        for alias, (expected_type, expected_subtype) in aliases.items():
            with self.subTest(alias=alias):
                result = normalize_sv_input(json.dumps({
                    "genome_build": "hg38", "chrom": "1", "start": 100,
                    "end": 100, "sv_type": alias, "length_bp": 300,
                }))
                self.assertEqual(result["status"], "valid")
                self.assertEqual(result["sv_type"], expected_type)
                self.assertEqual(result["sv_subtype"], expected_subtype)
                self.assertEqual(result["sv_type_original"], alias)

    def test_normalize_rejects_non_integer_coordinates(self):
        for value in (1.5, "1.0", True):
            with self.subTest(value=value):
                result = normalize_sv_input(json.dumps({
                    "genome_build": "GRCh38", "chrom": "1", "start": value,
                    "end": 10, "sv_type": "DUP",
                }))
                self.assertEqual(result["status"], "validation_error")
                self.assertIn("start must be an integer", result["error"])

    def test_normalize_checks_chromosome_boundaries(self):
        valid = normalize_sv_input(json.dumps({
            "genome_build": "hg38", "chrom": "chr1", "start": 248956422,
            "end": 248956422, "sv_type": "DEL",
        }))
        self.assertEqual(valid["status"], "valid")
        self.assertEqual(valid["chromosome_length_bp"], 248956422)

        invalid = normalize_sv_input(json.dumps({
            "genome_build": "hg38", "chrom": "chr1", "start": 248956422,
            "end": 248956423, "sv_type": "DEL",
        }))
        self.assertEqual(invalid["status"], "validation_error")
        self.assertIn("exceed GRCh38 chromosome 1 length", invalid["error"])

    def test_normalize_validates_and_reconciles_lengths(self):
        invalid = normalize_sv_input(json.dumps({
            "genome_build": "hg19", "chrom": "2", "start": 100,
            "end": 100, "sv_type": "ALU", "length_bp": -1,
        }))
        self.assertEqual(invalid["status"], "validation_error")
        self.assertIn("length_bp must be a positive integer", invalid["error"])

        deletion = normalize_sv_input(json.dumps({
            "genome_build": "hg19", "chrom": "2", "start": 100,
            "end": 199, "sv_type": "DEL", "svlen": -99,
        }))
        self.assertEqual(deletion["status"], "valid")
        self.assertEqual(deletion["length_bp"], 100)
        self.assertIn(
            "provided_length_does_not_match_inclusive_coordinates",
            deletion["warnings"],
        )

    def test_normalize_carries_vcf_breakpoint_confidence_intervals(self):
        result = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL", "CIPOS": "-20,30",
            "source_record": {"INFO": {"CIEND": [-40, 50], "IMPRECISE": True}},
        }))
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["cipos"], [-20, 30])
        self.assertEqual(result["ciend"], [-40, 50])
        self.assertEqual(result["start_confidence_interval"], [980, 1030])
        self.assertEqual(result["end_confidence_interval"], [1960, 2050])
        self.assertEqual(result["breakpoint_uncertainty_status"], "complete")
        self.assertTrue(result["imprecise"])

    def test_normalize_marks_missing_breakpoint_uncertainty(self):
        result = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }))
        self.assertEqual(result["breakpoint_uncertainty_status"], "not_provided")
        self.assertIsNone(result["start_confidence_interval"])
        self.assertIn(
            "breakpoint_confidence_intervals_not_provided", result["warnings"]
        )

    def test_normalize_bnd_alt_retains_mate_and_orientation(self):
        forms = {
            "N[chr2:3000[": ("+", "+"),
            "N]chr2:3000]": ("+", "-"),
            "[chr2:3000[N": ("-", "+"),
            "]chr2:3000]N": ("-", "-"),
        }
        for alt, orientations in forms.items():
            with self.subTest(alt=alt):
                result = normalize_sv_input(json.dumps({
                    "genome_build": "hg38", "chrom": "1", "start": 1000,
                    "end": 1000, "sv_type": "BND", "ALT": alt,
                    "CIPOS": [-5, 5], "CIEND": [-10, 20],
                }))
                self.assertEqual(result["status"], "valid")
                self.assertEqual(result["bnd_mate_status"], "coordinates_provided")
                self.assertEqual(result["mate_chrom"], "2")
                self.assertEqual(result["mate_pos"], 3000)
                self.assertEqual(result["mate_confidence_interval"], [2990, 3020])
                self.assertEqual(
                    (result["local_orientation"], result["mate_orientation"]),
                    orientations,
                )

    def test_normalize_legacy_or_bad_optional_bnd_mate_stays_valid(self):
        legacy = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 1000, "sv_type": "BND",
        }))
        self.assertEqual(legacy["status"], "valid")
        self.assertEqual(legacy["bnd_mate_status"], "not_provided")

        malformed_optional = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 1000, "sv_type": "BND", "ALT": "<BND>",
            "chrom2": "not-a-chromosome", "pos2": "bad",
        }))
        self.assertEqual(malformed_optional["status"], "valid")
        self.assertEqual(malformed_optional["bnd_mate_status"], "not_provided")
        self.assertIn(
            "explicit_BND_mate_invalid_and_ignored", malformed_optional["warnings"]
        )

    def test_normalize_rejects_bad_coordinates(self):
        result = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 20,
            "end": 10, "sv_type": "DUP",
        }))
        self.assertEqual(result["status"], "validation_error")
        self.assertIn("start <= end", result["error"])

    def test_missing_quality_stays_unknown(self):
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh37", "chrom": "X", "start": 1,
            "end": 10, "sv_type": "INV",
        }))
        risks = assess_artifact_risk(json.dumps(sv))
        call_rate = next(x for x in risks["risk_items"] if x["risk_type"] == "low_call_rate")
        self.assertEqual(call_rate["status"], "unknown")

    def test_invalid_numeric_quality_values_stay_unknown(self):
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1,
            "end": 10, "sv_type": "DEL",
            "quality": {
                "call_rate": 1.5,
                "supporting_reads": True,
                "genotype_quality": False,
            },
        }))
        risks = assess_artifact_risk(json.dumps(sv))["risk_items"]
        by_type = {item["risk_type"]: item for item in risks}
        self.assertEqual(by_type["low_call_rate"]["status"], "unknown")
        self.assertEqual(by_type["supporting_reads"]["status"], "unknown")
        self.assertEqual(by_type["genotype_quality"]["status"], "unknown")

    def test_database_adapters_revalidate_stored_coordinates(self):
        forged = json.dumps({
            "status": "valid", "genome_build": "GRCh38", "chrom": "1",
            "start": 1, "end": 248956423, "sv_type": "DEL",
        })
        result = query_gnomad_sv(forged)
        self.assertEqual(result["status"], "error")
        self.assertIn("chromosome length", result["error"])

        ensembl = query_ensembl_region(
            "GRCh38", "1", 1, 248956423, "DEL"
        )
        self.assertEqual(ensembl["status"], "error")
        self.assertIn("chromosome length", ensembl["error"])

    def test_report_renderer_keeps_evidence_ids(self):
        markdown = render_markdown({
            "report_status": "incomplete",
            "sv_summary": {
                "sv_id": "sv1", "genome_build": "GRCh38", "chrom": "1",
                "start": 10, "end": 20, "sv_type": "DEL",
            },
            "gene_region_annotation": [{
                "statement": "Overlaps a feature", "evidence_ids": ["ENS001"],
                "confidence": "high", "kind": "observation",
            }],
        })
        self.assertIn("ENS001", markdown)
        self.assertIn("incomplete", markdown)
        self.assertIn("| SV type | DEL |", markdown)
        self.assertIn("| Position | chr1:10-20 |", markdown)

    def test_report_renderer_summarizes_baseline_source_results(self):
        markdown = render_markdown({
            "report_status": "incomplete",
            "sv_summary": {
                "sv_id": "sv1", "genome_build": "GRCh38", "chrom": "1",
                "start": 10, "end": 20, "sv_type": "DEL",
            },
            "query_provenance": [
                {"source": "gnomAD-SV", "status": "found"},
                {"source": "ClinVar", "status": "not_found"},
                {"source": "PubMed", "status": "found"},
            ],
        })
        self.assertIn("## Baseline source checks", markdown)
        self.assertIn("| gnomAD-SV | Found |", markdown)
        self.assertIn("| ClinVar | No record found |", markdown)
        self.assertNotIn("| PubMed | Found |", markdown)

    def test_report_renderer_keeps_partial_claim_with_qualification(self):
        markdown = render_markdown({
            "report_status": "incomplete",
            "sv_summary": {},
            "verified_claims": [{
                "text": "A nearby candidate may represent the same event.",
                "evidence_ids": ["GNO-BL-001"],
                "verification_status": "partially_supported",
                "notes": "The start coordinate differs by 1 bp.",
            }],
        })
        self.assertIn("## Qualified findings", markdown)
        self.assertIn("The start coordinate differs by 1 bp.", markdown)

    def test_report_renderer_shows_normalization_metadata(self):
        markdown = render_markdown({
            "report_status": "incomplete",
            "sv_summary": {
                "sv_id": "sv2", "genome_build": "GRCh38",
                "genome_build_original": "hg38", "chrom": "1",
                "start": 100, "end": 100,
                "coordinate_system": "1-based-inclusive",
                "breakpoint_uncertainty_status": "complete",
                "start_confidence_interval": [90, 110],
                "end_confidence_interval": [95, 105],
                "sv_type": "INS", "sv_type_original": "ALU",
                "sv_subtype": "ALU", "length_bp": 300,
            },
        })
        self.assertIn("1-based-inclusive", markdown)
        self.assertIn("`hg38` → `GRCh38`", markdown)
        self.assertIn("`ALU` → `INS`", markdown)
        self.assertIn("start CI=[90, 110]", markdown)

    def test_report_schema_rejects_dangling_evidence_id(self):
        with self.assertRaises(ValueError):
            SVReport.model_validate({
                "report_status": "incomplete",
                "sv_summary": {
                    "validation_status": "valid", "sv_id": "sv1",
                    "genome_build": "GRCh38", "chrom": "1", "start": 10,
                    "end": 20, "sv_type": "DEL",
                },
                "gene_region_annotation": [{
                    "statement": "Overlaps a feature", "evidence_ids": ["ENS404"],
                    "confidence": "high", "kind": "observation",
                }],
            })

    def test_report_schema_counts_only_executed_actions_against_budget(self):
        report = SVReport.model_validate({
            "report_status": "incomplete",
            "sv_summary": {
                "validation_status": "valid", "sv_id": "sv1",
                "genome_build": "GRCh38", "chrom": "1", "start": 10,
                "end": 20, "sv_type": "DEL",
            },
            "investigation_log": {
                "executed_actions": [
                    {"action": "bad", "status": "rejected"},
                    {"action": "QUERY_EXONS", "status": "executed"},
                ],
                "query_budget": 2,
                "queries_used": 1,
                "stop_reason": "budget decision complete",
            },
        })
        self.assertEqual(len(report.investigation_log.executed_actions), 2)

    def test_report_schema_derives_budget_fields_from_executed_actions(self):
        report = SVReport.model_validate({
            "report_status": "incomplete",
            "sv_summary": {
                "validation_status": "valid", "sv_id": "sv1",
                "genome_build": "GRCh38", "chrom": "1", "start": 10,
                "end": 20, "sv_type": "DEL",
            },
            "investigation_log": {
                "executed_actions": [
                    {"action": "QUERY_EXONS", "status": "executed"},
                    {"action": "duplicate", "status": "rejected"},
                ],
                # Model-written counters are ignored in favor of the audit list.
                "query_budget": 0,
                "queries_used": 99,
                "stop_reason": "test deterministic derivation",
            },
        })
        self.assertEqual(report.investigation_log.query_budget, 2)
        self.assertEqual(report.investigation_log.queries_used, 1)

    def test_report_schema_preserves_not_applicable_source_status(self):
        report = SVReport.model_validate({
            "report_status": "incomplete",
            "sv_summary": {
                "validation_status": "valid", "sv_id": "bnd1",
                "genome_build": "GRCh38", "chrom": "1", "start": 10,
                "end": 10, "sv_type": "BND",
            },
            "query_provenance": [{
                "source": "Ensembl VEP", "status": "not_applicable",
                "query_summary": "BND adjacency is not supported by this endpoint",
            }],
            "investigation_log": {
                "query_budget": 2, "queries_used": 0,
                "stop_reason": "baseline source not applicable",
            },
        })
        self.assertEqual(report.query_provenance[0].status, "not_applicable")

    @patch("sv_investigator.tools._json_request")
    def test_ensembl_region_preserves_sv_type_and_query_scope(self, request):
        request.side_effect = [
            ([{"id": "ENSG1"}], None),
            ([], None),
            ([], None),
        ] + [( [], None)] * 6
        result = query_ensembl_region("GRCh38", "1", 10, 20, "deletion")
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["completeness"], "complete")
        self.assertEqual(result["sv_type"], "DEL")
        self.assertEqual(result["annotation_mode"], "spatial_overlap_only")
        self.assertIn("?feature=gene", result["source_urls"]["gene"])
        self.assertEqual(
            result["breakpoint_annotations"]["start"]["source"],
            "heuristic_fallback",
        )

    @patch("sv_investigator.tools._json_request")
    def test_ensembl_partial_failure_is_not_not_found(self, request):
        def response(url, params, headers, **kwargs):
            del headers, kwargs
            if params["feature"] == "repeat" and "1:10-20" not in url:
                return None, "HTTP 503"
            return [], None

        request.side_effect = response
        result = query_ensembl_region("GRCh38", "1", 10, 20, "DEL")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["completeness"], "partial")
        self.assertIsNone(
            result["breakpoint_annotations"]["start"]["features"]["repeat"]
        )
        self.assertEqual(result["breakpoint_annotations"]["start"]["attempts"]["repeat"], 2)

        risks = assess_artifact_risk(json.dumps({
            "quality": {},
        }), json.dumps(result))
        repeat = next(
            item for item in risks["risk_items"]
            if item["risk_type"] == "repeat_region"
        )
        self.assertEqual(repeat["status"], "unknown")

    @patch("sv_investigator.tools._json_request")
    def test_ensembl_bnd_queries_parsed_mate_breakend(self, request):
        request.return_value = ([], None)
        result = query_ensembl_region(
            "GRCh38", "1", 1000, 1000, "BND", [995, 1005], [995, 1005],
            "2", 3000, [2990, 3010],
        )
        mate = result["breakpoint_annotations"]["mate"]
        self.assertIsNotNone(mate)
        self.assertEqual(mate["query_region"], "2:2990-3010")
        self.assertEqual(mate["source"], "vcf_confidence_interval")
        self.assertTrue(any("/2:2990-3010" in call.args[0] for call in request.call_args_list))

    @patch("sv_investigator.tools._json_request")
    def test_ensembl_reuses_identical_query_scopes(self, request):
        request.return_value = ([], None)
        result = query_ensembl_region(
            "GRCh38", "1", 1000, 1000, "INS", [1000, 1000], [1000, 1000]
        )
        self.assertEqual(result["status"], "not_found")
        # Nominal, start and end all resolve to the same interval: three feature
        # requests are sufficient instead of repeating them for every role.
        self.assertEqual(request.call_count, 3)

    @patch("sv_investigator.tools._json_post")
    def test_gnomad_sv_uses_build_matched_dataset_and_match_metrics(self, post):
        post.return_value = ({"data": {"region": {"structural_variants": [{
            "variant_id": "DEL_chr1_example", "chrom": "1", "chrom2": "1",
            "pos": 990, "end": 2020, "pos2": None, "end2": None,
            "length": 1031, "type": "DEL", "consequence": "lof",
            "ac": 4, "an": 100000, "af": 0.00004, "ac_hom": 0,
            "ac_hemi": 0, "filters": [],
        }]}}}, None)
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL", "CIPOS": [-20, 20],
            "CIEND": [-30, 30],
        }))
        result = query_gnomad_sv(json.dumps(sv))
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["dataset"], "gnomad_sv_r4")
        self.assertEqual(result["records"][0]["match_type"], "high_similarity")
        self.assertEqual(
            result["records"][0]["match_metrics"]["start_window_source"],
            "vcf_confidence_interval",
        )
        self.assertFalse(result["records"][0]["same_event_established"])

    @patch("sv_investigator.tools._json_post")
    def test_gnomad_sv_missing_ci_uses_labeled_fallback(self, post):
        post.return_value = ({"data": {"region": {"structural_variants": []}}}, None)
        sv = normalize_sv_input(json.dumps({
            "genome_build": "hg19", "chrom": "2", "start": 1000,
            "end": 2000, "sv_type": "DUP",
        }))
        result = query_gnomad_sv(json.dumps(sv))
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["dataset"], "gnomad_sv_r2_1")
        self.assertEqual(
            result["breakpoint_windows"]["start"]["source"],
            "heuristic_fallback",
        )
        self.assertFalse(
            result["breakpoint_windows"]["start"]["is_measured_confidence_interval"]
        )

    @patch("sv_investigator.tools._json_post")
    def test_gnomad_missing_ci_fallback_does_not_inflate_similarity(self, post):
        post.return_value = ({"data": {"region": {"structural_variants": [{
            "variant_id": "DEL_nearby", "chrom": "1", "chrom2": "1",
            "pos": 1010, "end": 2010, "pos2": None, "end2": None,
            "length": 1001, "type": "DEL", "consequence": None,
            "ac": 1, "an": 1000, "af": 0.001, "ac_hom": 0,
            "ac_hemi": 0, "filters": [],
        }]}}}, None)
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }))
        record = query_gnomad_sv(json.dumps(sv))["records"][0]
        self.assertEqual(record["match_type"], "partial_overlap")
        self.assertFalse(record["match_metrics"]["start_within_allowed_window"])
        self.assertFalse(record["match_metrics"]["end_within_allowed_window"])
        self.assertEqual(
            record["match_metrics"]["start_window_source"], "heuristic_fallback"
        )
        self.assertFalse(record["same_event_established"])

    @patch("sv_investigator.tools._json_post")
    def test_expanded_retrieval_does_not_expand_matching_window(self, post):
        post.return_value = ({"data": {"region": {"structural_variants": [{
            "variant_id": "DEL_far", "chrom": "1", "chrom2": "1",
            "pos": 2500, "end": 3500, "pos2": None, "end2": None,
            "length": 1001, "type": "DEL", "consequence": None,
            "ac": 1, "an": 1000, "af": 0.001, "ac_hom": 0,
            "ac_hemi": 0, "filters": [],
        }]}}}, None)
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL", "CIPOS": [-10, 10],
            "CIEND": [-10, 10],
        }))
        result = query_gnomad_sv(json.dumps(sv), retrieval_padding_bp=2000)
        variables = post.call_args.args[1]["variables"]
        self.assertEqual(variables["start"], 1)
        self.assertEqual(variables["stop"], 4010)
        self.assertTrue(result["matching_windows_unchanged"])
        self.assertEqual(result["retrieval_padding_bp"], 2000)
        self.assertEqual(result["records"][0]["match_type"], "nearby")

    @patch("sv_investigator.tools._text_request")
    def test_clingen_dosage_parses_current_csv_and_relevant_direction(self, request):
        request.return_value = (\
            '"CLINGEN DOSAGE SENSITIVITY CURATIONS (FULL)"\n'
            '"FILE CREATED: 2026-09-18"\n'
            '"GENE/REGION","HGNC/ISCA","GRCh37","GRCh38",'
            '"HAPLOINSUFFICIENCY","TRIPLOSENSITIVITY","ONLINE REPORT","DATE"\n'
            '"test region","ISCA-1","chr1:900-2100","chr1:900-2100",'
            '"Sufficient Evidence for Haploinsufficiency",'
            '"No Evidence for Triplosensitivity","https://example.test/ISCA-1",'
            '"2026-01-01"\n',
            None,
        )
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }))
        result = query_clingen_dosage(json.dumps(sv))
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["dataset_created_at"], "2026-09-18")
        record = result["records"][0]
        self.assertEqual(record["record_id"], "ISCA-1")
        self.assertEqual(record["relevant_dosage_direction"], "haploinsufficiency")
        self.assertEqual(record["haploinsufficiency"]["score"], 3)
        self.assertFalse(record["same_event_established"])

    @patch("sv_investigator.tools._json_request")
    def test_clinvar_retains_review_status_and_interval_metrics(self, request):
        request.side_effect = [
            ({"esearchresult": {"idlist": ["123"]}}, None),
            ({"result": {"uids": ["123"], "123": {
                "uid": "123", "obj_type": "Deletion",
                "accession": "VCV000000123", "accession_version": "VCV000000123.2",
                "title": "GRCh38 chr1 deletion", "variation_set": [{
                    "variant_type": "Deletion", "variation_loc": [{
                        "assembly_name": "GRCh38", "chr": "1",
                        "start": "990", "stop": "2020",
                        "inner_start": "", "inner_stop": "",
                        "outer_start": "", "outer_stop": "",
                        "assembly_acc_ver": "GCF_000001405.38",
                    }],
                }],
                "supporting_submissions": {"scv": ["SCV1", "SCV2"], "rcv": ["RCV1"]},
                "germline_classification": {
                    "description": "Pathogenic",
                    "review_status": "criteria provided, multiple submitters, no conflicts",
                    "last_evaluated": "2026/01/02 00:00",
                    "trait_set": [{"trait_name": "example disorder"}],
                },
                "genes": [{"symbol": "GENE1"}],
            }}}, None),
        ]
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL", "CIPOS": [-20, 20],
            "CIEND": [-30, 30],
        }))
        result = query_clinvar(json.dumps(sv))
        self.assertEqual(result["status"], "found")
        self.assertIn("50:100000000[varlen]", result["query_terms"][0])
        record = result["records"][0]
        self.assertEqual(record["record_id"], "VCV000000123.2")
        self.assertEqual(record["germline_classification"], "Pathogenic")
        self.assertEqual(record["supporting_scv_count"], 2)
        self.assertEqual(record["match_type"], "high_similarity")
        self.assertFalse(record["same_event_established"])

    @patch("sv_investigator.tools._json_request")
    def test_dgv_uses_zero_based_api_but_returns_one_based_compact_records(self, request):
        request.return_value = ({
            "dataTime": "2026-01-01", "dgvGold": [{
                "chrom": "chr1", "chromStart": 999, "chromEnd": 2000,
                "dgvID": "gssvG1", "variant_type": "CNV",
                "variant_sub_type": "Gain", "Frequency": "12.5%",
                "num_unique_samples_tested": 1000, "num_samples": 125,
                "num_studies": 2, "Studies": "StudyA, StudyB",
                "num_platforms": 1, "Platforms": "Array",
                "num_variants": 8,
                "variants": "v1, v2, v3, v4, v5, v6, v7, v8",
                "samples": "large sample list must not be copied",
            }],
        }, None)
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DUP",
        }))
        result = query_dgv(json.dumps(sv))
        self.assertEqual(result["status"], "found")
        params = request.call_args.args[1]
        self.assertEqual(params["start"], 499)
        record = result["records"][0]
        self.assertEqual((record["start"], record["end"]), (1000, 2000))
        self.assertEqual(record["match_type"], "exact")
        self.assertTrue(record["source_variant_ids_truncated"])
        self.assertNotIn("samples", record)

    @patch("sv_investigator.tools._ensembl_json_request")
    def test_vep_compacts_and_ranks_transcript_consequences(self, request):
        request.return_value = ([{
            "id": "1_1000_deletion", "assembly_name": "GRCh38",
            "seq_region_name": "1", "start": 1000, "end": 2000,
            "allele_string": "deletion",
            "most_severe_consequence": "transcript_ablation",
            "transcript_consequences": [{
                "gene_id": "ENSG2", "transcript_id": "ENST2",
                "impact": "MODIFIER", "consequence_terms": ["intron_variant"],
                "percentage_overlap": 5.0, "biotype": "lncRNA",
            }, {
                "gene_id": "ENSG1", "gene_symbol": "GENE1",
                "transcript_id": "ENST1", "impact": "HIGH",
                "consequence_terms": ["transcript_ablation"],
                "percentage_overlap": 100.0, "canonical": 1,
                "mane_select": "NM_000001.1", "biotype": "protein_coding",
            }],
        }], None, 1)
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }))
        result = query_ensembl_vep(json.dumps(sv))
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["records"][0]["transcript_id"], "ENST1")
        self.assertTrue(result["records"][0]["canonical"])
        self.assertEqual(result["input_annotations"][0]["most_severe_consequence"],
                         "transcript_ablation")
        self.assertIn("/vep/human/region/1:1000-2000:1/DEL", request.call_args.args[0])

    @patch("sv_investigator.tools._json_request")
    def test_dbvar_filters_build_and_labels_direction_ambiguity(self, request):
        request.side_effect = [
            ({"esearchresult": {"count": "1", "idlist": ["42"]}}, None),
            ({"result": {"uids": ["42"], "42": {
                "uid": "42", "obj_type": "VARIANT", "st": "nstd1",
                "sv": "nsv42", "dbvarvarianttypelist": ["copy number variation"],
                "dbvarplacementlist": [
                    {"chr": "1", "chr_start": 900, "chr_end": 1900,
                     "assembly": "GRCh37.p13", "assembly_accession": ""},
                    {"chr": "1", "chr_start": 1000, "chr_end": 2000,
                     "assembly": "GRCh38.p14", "assembly_accession": ""},
                ],
                "dbvarmethodlist": ["Sequencing"],
                "dbvarclinicalsignificancelist": [], "dbvargenelist": [],
                "dbvarpublicationlist": [], "variant_call_count": 1,
            }}}, None),
        ]
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }))
        result = query_dbvar(json.dumps(sv))
        self.assertEqual(result["status"], "found")
        record = result["records"][0]
        self.assertEqual(record["record_id"], "nsv42")
        self.assertEqual(record["assembly"], "GRCh38.p14")
        self.assertEqual(record["type_compatibility"], "ambiguous_cnv_direction")
        self.assertEqual(record["match_type"], "exact")
        self.assertFalse(record["same_event_established"])

    @patch("sv_investigator.tools._json_request")
    @patch("sv_investigator.tools._ensembl_json_request")
    def test_p1_tools_do_not_force_single_interval_semantics_onto_bnd(
        self, ensembl_request, ncbi_request
    ):
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 1000, "sv_type": "BND",
            "alt": "N]2:2000]",
        }))
        payload = json.dumps(sv)
        self.assertEqual(query_ensembl_vep(payload)["status"], "not_applicable")
        self.assertEqual(query_dbvar(payload)["status"], "not_applicable")
        ensembl_request.assert_not_called()
        ncbi_request.assert_not_called()

    def test_new_database_failures_are_not_reported_as_negative_results(self):
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }))
        payload = json.dumps(sv)
        with patch("sv_investigator.tools._text_request", return_value=(None, "TimeoutError")):
            clingen = query_clingen_dosage(payload)
        with patch("sv_investigator.tools._json_request", return_value=(None, "HTTP 503")):
            clinvar = query_clinvar(payload)
            dbvar = query_dbvar(payload)
            dgv = query_dgv(payload)
        with patch(
            "sv_investigator.tools._ensembl_json_request",
            return_value=(None, "TimeoutError", 2),
        ):
            vep = query_ensembl_vep(payload)

        self.assertEqual(clingen["status"], "error")
        self.assertEqual(clinvar["status"], "error")
        self.assertEqual(clinvar["completeness"], "failed")
        self.assertEqual(dgv["status"], "error")
        self.assertEqual(dgv["completeness"], "failed")
        self.assertEqual(dbvar["status"], "error")
        self.assertEqual(dbvar["completeness"], "failed")
        self.assertEqual(vep["status"], "error")

    def test_adaptive_action_whitelist_and_budget_are_enforced(self):
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 2000, "sv_type": "DEL",
        }))
        rejected = execute_adaptive_action(json.dumps(sv), "QUERY_ANYTHING")
        self.assertEqual(rejected["error"], "action_not_whitelisted")

        state = {}
        with patch("sv_investigator.tools.execute_adaptive_action") as execute:
            execute.return_value = {"status": "executed", "result": {}}
            first = run_budgeted_adaptive_action(
                json.dumps(sv), "QUERY_TRANSCRIPTS", "missing transcripts",
                "overlap detail is absent", "could refine affected elements", state,
            )
            duplicate = run_budgeted_adaptive_action(
                json.dumps(sv), "QUERY_TRANSCRIPTS", "same gap", "retry",
                "none", state,
            )
            second = run_budgeted_adaptive_action(
                json.dumps(sv), "QUERY_EXONS", "missing exons", "refine overlap",
                "could distinguish intronic from exonic overlap", state,
            )
            over_budget = run_budgeted_adaptive_action(
                json.dumps(sv), "QUERY_NEAREST_GENE_10KB", "no nearby gene",
                "search nearby", "could identify context", state,
            )
        self.assertEqual(first["status"], "executed")
        self.assertEqual(duplicate["rejection_reason"], "duplicate_action")
        self.assertEqual(second["queries_used"], 2)
        self.assertEqual(over_budget["rejection_reason"], "query_budget_exhausted")
        self.assertEqual(execute.call_count, 2)

    @patch("sv_investigator.tools.query_dgv")
    @patch("sv_investigator.tools.query_dbvar")
    @patch("sv_investigator.tools.query_clinvar")
    @patch("sv_investigator.tools.query_clingen_dosage")
    @patch("sv_investigator.tools.query_ensembl_vep")
    @patch("sv_investigator.tools.assess_artifact_risk")
    @patch("sv_investigator.tools.query_gnomad_sv")
    @patch("sv_investigator.tools.query_ensembl_region")
    def test_baseline_collection_adds_ids_without_losing_records(
        self, ensembl, gnomad, artifact, vep, clingen, clinvar, dbvar, dgv
    ):
        ensembl.return_value = {
            "source": "Ensembl", "status": "found",
            "features": {"gene": [{"id": "ENSG1", "extra": "kept"}]},
            "breakpoint_annotations": {},
        }
        gnomad.return_value = {
            "source": "gnomAD-SV", "status": "found",
            "records": [{"variant_id": "v1", "af": 0.1}],
        }
        vep.return_value = {
            "source": "Ensembl VEP", "status": "found",
            "records": [{"record_id": "ENST1"}],
        }
        clingen.return_value = {
            "source": "ClinGen Dosage", "status": "found",
            "records": [{"record_id": "ISCA-1"}],
        }
        clinvar.return_value = {
            "source": "ClinVar", "status": "found",
            "records": [{"record_id": "VCV1"}],
        }
        dbvar.return_value = {
            "source": "NCBI dbVar", "status": "found",
            "records": [{"record_id": "nsv1"}],
        }
        dgv.return_value = {
            "source": "DGV Gold Standard", "status": "found",
            "records": [{"record_id": "gssv1"}],
        }
        artifact.return_value = {"overall_risk": "unknown", "risk_items": []}
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 10,
            "end": 20, "sv_type": "DEL",
        }))
        result = collect_baseline_evidence(json.dumps(sv))
        gene = result["region_annotation"]["features"]["gene"][0]
        self.assertEqual(gene["extra"], "kept")
        self.assertTrue(gene["evidence_id"].startswith("ENS-BL"))
        self.assertEqual(
            result["database_evidence"]["records"][0]["evidence_id"],
            "GNO-BL-001",
        )
        self.assertEqual(
            result["clingen_dosage_evidence"]["records"][0]["evidence_id"],
            "CGD-BL-001",
        )
        self.assertEqual(
            result["clinvar_evidence"]["records"][0]["evidence_id"],
            "CLV-BL-001",
        )
        self.assertEqual(
            result["dgv_evidence"]["records"][0]["evidence_id"],
            "DGV-BL-001",
        )
        self.assertEqual(
            result["vep_evidence"]["records"][0]["evidence_id"],
            "VEP-BL-001",
        )
        self.assertEqual(
            result["dbvar_evidence"]["records"][0]["evidence_id"],
            "DBV-BL-001",
        )

    @patch("sv_investigator.tools._json_post")
    def test_gnomad_bnd_matches_both_breakends_in_swapped_order(self, post):
        row = {
            "variant_id": "BND_example", "chrom": "2", "chrom2": "1",
            "pos": 3010, "end": 3010, "pos2": 995, "end2": 995,
            "length": None, "type": "BND", "consequence": None,
            "ac": 2, "an": 100000, "af": 0.00002, "ac_hom": 0,
            "ac_hemi": 0, "filters": [],
        }
        post.return_value = (
            {"data": {"region": {"structural_variants": [row]}}}, None
        )
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 1000, "sv_type": "BND", "ALT": "N[2:3000[",
            "CIPOS": [-10, 10], "CIEND": [-20, 20],
        }))
        result = query_gnomad_sv(json.dumps(sv))
        self.assertEqual(result["query_strategy"], "paired_breakend_windows")
        self.assertEqual(len(post.call_args_list), 2)
        record = result["records"][0]
        self.assertEqual(record["match_type"], "high_similarity")
        self.assertEqual(
            record["match_metrics"]["database_breakend_order"],
            "swapped_relative_to_input",
        )
        self.assertEqual(record["match_metrics"]["comparison_scope"], "both_breakends")

    @patch("sv_investigator.tools._json_post")
    def test_gnomad_legacy_bnd_does_not_claim_same_event(self, post):
        post.return_value = ({"data": {"region": {"structural_variants": [{
            "variant_id": "BND_first_only", "chrom": "1", "chrom2": "2",
            "pos": 1000, "end": 1000, "pos2": 3000, "end2": 3000,
            "length": None, "type": "BND", "consequence": None,
            "ac": 1, "an": 100000, "af": 0.00001, "ac_hom": 0,
            "ac_hemi": 0, "filters": [],
        }]}}}, None)
        sv = normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "1", "start": 1000,
            "end": 1000, "sv_type": "BND",
        }))
        record = query_gnomad_sv(json.dumps(sv))["records"][0]
        self.assertEqual(record["match_type"], "high_similarity")
        self.assertEqual(record["match_metrics"]["comparison_scope"], "first_breakend_only")
        self.assertFalse(record["same_event_established"])

    @patch("sv_investigator.tools._json_request")
    def test_pubmed_metadata_retains_pmid_and_doi(self, request):
        request.side_effect = [
            ({"esearchresult": {"idlist": ["123"]}}, None),
            ({"result": {"123": {
                "title": "Example", "authors": [], "source": "Journal",
                "pubdate": "2025", "articleids": [
                    {"idtype": "doi", "value": "10.1/example"}
                ],
            }}}, None),
        ]
        result = search_pubmed("example structural variant")
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["records"][0]["pmid"], "123")
        self.assertEqual(result["records"][0]["doi"], "10.1/example")

    @patch("sv_investigator.tools._json_request")
    def test_pubmed_compacts_authors_and_caps_records(self, request):
        request.side_effect = [
            ({"esearchresult": {"idlist": ["123", "456"]}}, None),
            ({"result": {"123": {
                "title": "Example", "authors": [
                    {"name": "A", "authtype": "Author", "clusterid": "1"},
                    {"name": "B", "authtype": "Author", "clusterid": "2"},
                    {"name": "C", "authtype": "Author", "clusterid": "3"},
                    {"name": "D", "authtype": "Author", "clusterid": "4"},
                ], "articleids": [],
            }}}, None),
        ]
        result = search_pubmed("example", max_records=1)
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["authors"], ["A", "B", "C"])
        self.assertEqual(result["records"][0]["author_count"], 4)
        self.assertTrue(result["records"][0]["authors_truncated"])

    @patch("sv_investigator.tools._json_request")
    def test_pubmed_invalid_response_is_not_reported_as_no_results(self, request):
        request.return_value = ({"unexpected": "shape"}, None)
        result = search_pubmed("example")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "invalid_search_response_shape")


if __name__ == "__main__":
    unittest.main()
