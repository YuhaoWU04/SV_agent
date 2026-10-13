import json
import unittest
from unittest.mock import patch

from sv_investigator import tools
from sv_investigator.state_pipeline import build_evidence_view, _catalog_record


class FunctionalEvidenceTest(unittest.TestCase):
    def sv(self, **changes):
        return json.dumps(tools.normalize_sv_input(json.dumps({
            "genome_build": "GRCh38", "chrom": "3", "start": 1000,
            "end": 1050, "sv_type": "DEL", **changes,
        })))

    @patch("sv_investigator.tools._json_request")
    def test_ccre_coordinates_and_endpoint_only_links(self, request):
        request.return_value = ({"cCREregistry": [{"chrom": "chr3", "chromStart": 999,
            "chromEnd": 1050, "name": "EH1", "cCRE_class": "Distal enhancer"}]}, None)
        result = tools.query_functional_track(self.sv(), "ccre")
        self.assertEqual(result["records"][0]["start"], 1000)
        self.assertEqual(request.call_args.args[1]["start"], 999)
        request.return_value = ({"geneHancerInteractionsDoubleElite": [
            {"name": "GENE/decoy", "geneHancerChrom": "chr3",
             "geneHancerStart": 900, "geneHancerEnd": 999},
            {"name": "GENE/hit", "geneHancerChrom": "chr3",
             "geneHancerStart": 999, "geneHancerEnd": 1050,
             "geneName": "GENE", "geneAssociationMethods": "C-HiC"},
        ]}, None)
        links = tools.query_functional_track(self.sv(), "links")
        self.assertEqual([r["name"] for r in links["records"]], ["GENE/hit"])

    @patch("sv_investigator.tools._json_request")
    def test_qtl_connecting_span_is_not_variant_overlap(self, request):
        request.return_value = ({"gtexEqtlDapg": [
            {"name": "decoy", "eqtlPos": "chr3:50000-50000"},
            {"name": "hit", "eqtlPos": "chr3:1020-1020", "pip": "0.2", "tissue": "Liver"},
        ]}, None)
        result = tools.query_qtl_context(self.sv())
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["sv_identity"], "not_established")
        self.assertEqual(result["records"][0]["match_type"], "regional_qtl_context")
        region = result["query_regions"][0]
        self.assertEqual(region["scope"], "padded_nominal_interval")
        self.assertEqual(region["padding_bp"], 10000)
        self.assertEqual((region["start"], region["end"]), (1, 11050))
        self.assertEqual(result["records"][0]["query_scope"], region["scope"])

    @patch("sv_investigator.tools._json_request")
    def test_record_cap_and_returned_count_agree(self, request):
        request.return_value = ({"cCREregistry": [
            {"chrom": "chr3", "chromStart": 999, "chromEnd": 1050, "name": name}
            for name in ("EH1", "EH2")
        ]}, None)
        with patch("sv_investigator.tools.MAX_DATABASE_RECORDS", 1):
            result = tools.query_functional_track(self.sv(), "ccre")
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["returned_record_count"], 1)
        self.assertTrue(result["records_truncated"])
        self.assertEqual(result["completeness"], "partial")

    @patch("sv_investigator.tools._json_request")
    def test_malformed_feature_coordinates_keep_other_records(self, request):
        request.return_value = ({"cCREregistry": [
            {"chrom": None, "chromStart": 999, "chromEnd": 1050, "name": "broken"},
            {"chrom": "chr3", "chromStart": 999, "chromEnd": 1050, "name": "valid"},
        ]}, None)
        result = tools.query_functional_track(self.sv(), "ccre")
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["completeness"], "partial")
        self.assertEqual([row["name"] for row in result["records"]], ["valid"])
        self.assertIn("invalid_feature_coordinates", result["query_errors"][0]["error"])

    @patch("sv_investigator.tools._json_request")
    def test_malformed_sqtl_rows_do_not_discard_valid_context(self, request):
        request.side_effect = [
            ({"gtexEqtlDapg": [{"eqtlName": "rs1", "eqtlPos": "chr3:1020-1020"}]}, None),
            ({"data": [None, {"variantId": "chr3_1020_A_G_b38", "chromosome": "chr3", "pos": 1020}]}, None),
            ({"data": [None, {"variantId": "chr3_1020_A_G_b38", "geneSymbol": "GENE"}],
              "paging_info": {"numberOfPages": 1}}, None),
        ]
        result = tools.query_qtl_context(self.sv())
        self.assertEqual(result["completeness"], "partial")
        self.assertEqual(result["records"][-1]["geneSymbol"], "GENE")
        self.assertEqual([row["error"] for row in result["query_errors"]],
                         ["invalid_variant_record", "unexpected_sqtl_variant"])

    @patch("sv_investigator.tools._json_request")
    def test_sqtl_followup_keeps_tissue_alleles_and_statistics(self, request):
        request.side_effect = [
            ({"gtexEqtlDapg": [{"name": "rs1/GENE/Liver", "eqtlName": "rs1",
                                "eqtlPos": "chr3:1020-1020", "pip": "0.2"}]}, None),
            ({"data": [{"variantId": "chr3_1020_A_G_b38", "chromosome": "chr3",
                        "pos": 1020, "ref": "A", "alt": "G"}]}, None),
            ({"data": [{"variantId": "chr3_1020_A_G_b38", "geneSymbol": "GENE",
                        "phenotypeId": "intron1", "tissueSiteDetailId": "Liver",
                        "pValue": 0.001, "nes": -0.5}], "paging_info": {"numberOfPages": 1}}, None),
        ]
        result = tools.query_qtl_context(self.sv())
        self.assertEqual(result["completeness"], "complete")
        row = result["records"][-1]
        self.assertEqual((row["qtl_type"], row["alt"], row["nes"]), ("sQTL", "G", -0.5))
        self.assertEqual(row["sv_identity"], "not_established")
        enriched = tools._add_evidence_ids(result, "QTL-BL")
        entry = _catalog_record("QTL-BL-002", {"record": enriched["records"][-1], "context": result}, ["C2"])
        self.assertEqual(entry["key_facts"]["phenotypeId"], "intron1")

    @patch("sv_investigator.tools._json_request")
    def test_mappability_weighting_and_missing_data(self, request):
        request.return_value = ({"umap100Quantitative": [
            {"start": 999, "end": 1001, "value": 1},
            {"start": 1001, "end": 1003, "value": 0.5},
        ]}, None)
        sv = self.sv(CIPOS=[0, 3], CIEND=[0, 0])
        result = tools.query_functional_track(sv, "map")
        first, second = result["records"]
        self.assertEqual(first["mean"], 0.75)
        self.assertEqual(first["coverage_fraction"], 1)
        self.assertIsNone(second["mean"])
        self.assertEqual(second["unmeasured_bases"], 1)
        risks = tools.assess_artifact_risk(sv, mappability_json=json.dumps(result))
        risk = next(r for r in risks["risk_items"] if r["risk_type"] == "low_mappability")
        self.assertEqual(risk["status"], "unknown")
        self.assertEqual(risk["evidence"][0]["mean"], 0.75)

    @patch("sv_investigator.tools._json_request")
    def test_failure_build_and_truncation_are_explicit(self, request):
        self.assertEqual(tools.query_qtl_context(self.sv(genome_build="GRCh37"))["status"], "not_applicable")
        request.assert_not_called()
        request.return_value = (None, "HTTP 503")
        self.assertEqual(tools.query_functional_track(self.sv(), "ccre")["status"], "error")
        request.return_value = ({"cCREregistry": [], "maxItemsLimit": True}, None)
        result = tools.query_functional_track(self.sv(), "ccre")
        self.assertEqual(result["completeness"], "partial")

    @patch("sv_investigator.tools._json_request")
    def test_bnd_mate_and_downstream_evidence(self, request):
        request.return_value = ({"umap100Quantitative": []}, None)
        result = tools.query_functional_track(self.sv(sv_type="BND", end=1000, ALT="N[2:2000["), "map")
        self.assertEqual([r["chrom"] for r in result["query_regions"]], ["3", "2"])
        result = tools._add_evidence_ids(result, "MAP-BL")
        view = build_evidence_view({"baseline_evidence": {"mappability_evidence": result}})
        self.assertIn("MAP-BL-001", view["records_by_id"])
        entry = _catalog_record("MAP-BL-001", {"record": result["records"][0], "context": result}, ["C1"])
        self.assertEqual(entry["evidence_type"], "reference_mappability")
        self.assertEqual(entry["key_facts"]["unmeasured_bases"], 1001)
        local_only = tools.query_functional_track(self.sv(sv_type="BND", end=1000), "map")
        self.assertEqual(local_only["completeness"], "partial")


if __name__ == "__main__":
    unittest.main()
