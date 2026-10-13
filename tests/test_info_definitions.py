import json
import unittest

from sv_investigator.info_definitions import query_info_descriptions, resolve_info_definitions
from sv_investigator.state_pipeline import normalize_and_store
from sv_investigator.tools import normalize_sv_input


class InfoDefinitionTests(unittest.TestCase):
    def test_lookup_pairs_values_with_saved_descriptions_and_preserves_state(self):
        normalized = normalize_sv_input(json.dumps({"genome_build": "GRCh38", "chrom": "1",
            "start": 100, "end": 200, "sv_type": "DEL", "source_record": {
                "dataset": "1000G-SV", "INFO": {"MC": ["call1"], "NS": "4"}}}))
        original = json.dumps(normalized, sort_keys=True)
        result = query_info_descriptions(normalized, ["MC", "NS", "MC"])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(list(result["fields"]), ["MC", "NS"])
        self.assertEqual(result["fields"]["MC"], {"value": ["call1"],
                          "description": "Merged calls.", "source": "1000g_dictionary"})
        self.assertEqual(result["fields"]["NS"]["value"], "4")
        result["fields"]["MC"]["value"].append("changed")
        self.assertEqual(json.dumps(normalized, sort_keys=True), original)

    def test_lookup_distinguishes_absent_fields_from_missing_descriptions(self):
        normalized = normalize_sv_input(json.dumps({"genome_build": "GRCh38", "chrom": "1",
            "start": 100, "end": 200, "sv_type": "DEL",
            "source_record": {"info": {"MC": "custom_value", "NS": "4"}}}))
        result = query_info_descriptions(normalized, ["MC", "NS", "MISSING", "ns"])
        self.assertEqual(result["undefined_fields"], ["MC"])
        self.assertEqual(result["missing_fields"], ["MISSING", "ns"])
        self.assertEqual(result["fields"]["MC"],
                         {"value": "custom_value", "description": None, "source": None})
        self.assertEqual(result["fields"]["NS"]["source"], "vcf_standard")

    def test_lookup_validates_requests_and_does_not_guess_for_old_state(self):
        for field_ids in ([], "NS", None, [1], [" "]):
            with self.subTest(field_ids=field_ids):
                self.assertEqual(query_info_descriptions({}, field_ids)["status"], "rejected")
        self.assertEqual(query_info_descriptions({}, ["NS"])["status"], "unavailable")
        old = {"source_record": {"INFO": {"NS": "4"}}}
        result = query_info_descriptions(old, ["NS"])
        self.assertEqual(result["undefined_fields"], ["NS"])
        self.assertIsNone(result["fields"]["NS"]["description"])

    def test_provided_overrides_dictionaries_and_only_present_fields_are_retained(self):
        result = resolve_info_definitions(
            {"MC": "call1", "NS": "4", "CUSTOM": "value"},
            {"MC": "Input-specific meaning", "CUSTOM": "Custom description", "ABSENT": "Unused"},
            "1000G-SV",
        )
        self.assertEqual(result["MC"], {"description": "Input-specific meaning", "source": "provided"})
        self.assertEqual(result["NS"], {"description": "Number of samples with data", "source": "1000g_dictionary"})
        self.assertEqual(result["CUSTOM"]["source"], "provided")
        self.assertNotIn("ABSENT", result)

    def test_known_dataset_then_standard_fallback(self):
        result = resolve_info_definitions({"MC": "call1", "DP": "100"}, dataset="1000g-sv")
        self.assertEqual(result["MC"], {"description": "Merged calls.", "source": "1000g_dictionary"})
        self.assertEqual(result["DP"]["source"], "vcf_standard")

    def test_unknown_dataset_does_not_guess_custom_abbreviations(self):
        for dataset in (None, "another_dataset"):
            with self.subTest(dataset=dataset):
                result = resolve_info_definitions({"NS": "4", "MC": "x", "UNKNOWN": "y"}, dataset=dataset)
                self.assertEqual(set(result), {"NS"})
                self.assertEqual(result["NS"]["source"], "vcf_standard")

    def test_structured_input_description_does_not_authenticate_its_origin_label(self):
        result = resolve_info_definitions({"MC": "x"}, {
            "MC": {"description": "Caller-supplied description", "source": "vcf_standard"},
        })
        self.assertEqual(result["MC"], {"description": "Caller-supplied description", "source": "provided"})

    def test_normalize_preserves_info_and_exposes_definitions_in_state(self):
        for info_key in ("INFO", "info"):
            with self.subTest(info_key=info_key):
                payload = {"genome_build": "GRCh38", "chrom": "1", "start": 100, "end": 200,
                           "sv_type": "DEL", "source_record": {"dataset": "1000G-SV",
                               info_key: {"MC": "call1", "NS": "4", "CIPOS": "-5,0", "UNKNOWN": "x"},
                               "info_definition": {"MC": "Input definition"}}}
                original = json.dumps(payload, sort_keys=True)
                state = {}
                result = normalize_and_store(json.dumps(payload), state)
                self.assertEqual(result["status"], "valid")
                self.assertEqual(result["cipos"], [-5, 0])
                self.assertEqual(result["source_record"][info_key], payload["source_record"][info_key])
                self.assertEqual(result["source_record"]["info_definition"]["MC"]["source"], "provided")
                self.assertEqual(state["normalized_sv"]["source_record"]["info_definition"],
                                 result["source_record"]["info_definition"])
                self.assertNotIn("UNKNOWN", result["source_record"]["info_definition"])
                self.assertEqual(json.dumps(payload, sort_keys=True), original)

    def test_plain_sv_needs_no_info_dictionary(self):
        result = normalize_sv_input(json.dumps({"genome_build": "GRCh38", "chrom": "1",
                                               "start": 100, "end": 200, "sv_type": "DEL"}))
        self.assertEqual(result["status"], "valid")
        self.assertIsNone(result["source_record"])
        self.assertEqual(resolve_info_definitions({}), {})

    def test_malformed_description_is_not_silently_used(self):
        for definitions in ([], {"NS": 4}, {"NS": ""}, {"NS": {"description": None}}):
            with self.subTest(definitions=definitions):
                result = normalize_sv_input(json.dumps({"genome_build": "GRCh38", "chrom": "1",
                    "start": 100, "end": 200, "sv_type": "DEL",
                    "source_record": {"INFO": {"NS": "4"}, "info_definition": definitions}}))
                self.assertEqual(result["status"], "validation_error")
                self.assertIn("info_definition", result["error"])


if __name__ == "__main__":
    unittest.main()
