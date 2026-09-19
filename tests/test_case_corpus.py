import json
import unittest
from pathlib import Path

from sv_investigator.tools import normalize_sv_input


CASE_ROOT = Path(__file__).parent / "cases"


class CaseCorpusTest(unittest.TestCase):
    """Keep test inputs valid, traceable, and isolated from hidden answers."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = cls._read_json(CASE_ROOT / "manifest.json")

    @staticmethod
    def _read_json(path: Path):
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def test_manifest_has_both_validation_layers_and_unique_ids(self):
        cases = self.manifest["cases"]
        case_ids = [case["case_id"] for case in cases]
        categories = {case["category"] for case in cases}

        self.assertEqual(len(case_ids), len(set(case_ids)))
        self.assertEqual(
            categories, {"technical_benchmark", "interpretation_reference"}
        )
        self.assertEqual(len(cases), 6)

    def test_all_referenced_files_exist_and_case_ids_match(self):
        for case in self.manifest["cases"]:
            with self.subTest(case_id=case["case_id"]):
                input_path = CASE_ROOT / case["input"]
                expected_path = CASE_ROOT / case["expected"]
                provenance_path = CASE_ROOT / case["provenance"]

                self.assertTrue(input_path.is_file())
                self.assertTrue(expected_path.is_file())
                self.assertTrue(provenance_path.is_file())
                self.assertEqual(
                    self._read_json(expected_path)["case_id"], case["case_id"]
                )

    def test_inputs_normalize_to_hidden_expected_identity(self):
        identity_keys = (
            "genome_build", "chrom", "start", "end", "sv_type", "length_bp"
        )
        for case in self.manifest["cases"]:
            with self.subTest(case_id=case["case_id"]):
                payload = self._read_json(CASE_ROOT / case["input"])
                expected = self._read_json(CASE_ROOT / case["expected"])
                normalized = normalize_sv_input(json.dumps(payload))

                self.assertEqual(normalized["status"], "valid", normalized)
                for key in identity_keys:
                    self.assertEqual(
                        normalized[key], expected["expected_normalized"][key]
                    )
                self.assertEqual(
                    normalized["breakpoint_uncertainty_status"],
                    expected["expected_normalized"][
                        "breakpoint_uncertainty_status"
                    ],
                )

    def test_hidden_reference_is_not_leaked_into_inputs(self):
        forbidden_keys = {
            "hidden_reference",
            "clinical_significance",
            "dosage_score",
            "evidence_strength",
            "expected_normalized",
            "automatable_checks",
            "manual_review_checks",
        }
        for case in self.manifest["cases"]:
            with self.subTest(case_id=case["case_id"]):
                payload = self._read_json(CASE_ROOT / case["input"])
                serialized = json.dumps(payload)
                for key in forbidden_keys:
                    self.assertNotIn(f'"{key}"', serialized)

    def test_missing_ci_is_omitted_not_encoded_as_zero_width(self):
        for case in self.manifest["cases"]:
            with self.subTest(case_id=case["case_id"]):
                payload = self._read_json(CASE_ROOT / case["input"])
                self.assertNotIn("CIPOS", payload)
                self.assertNotIn("CIEND", payload)


if __name__ == "__main__":
    unittest.main()
