from __future__ import annotations

import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from sv_investigator.population_fst import (
    Variant,
    bh_fdr,
    build_statistical_context,
    calculate,
    hudson_fst,
    load_panel,
    parse_region,
    read_vcf_region,
    write_outputs,
)
from sv_investigator.tools import normalize_sv_input


class PopulationFstTests(unittest.TestCase):
    def test_fst_first_selection_filter_ties_and_output_ranks(self) -> None:
        ids = ["q_tie_b", "below_mean", "fst_first", "bad_q", "zero", "q_tie_a", "lower_q", "low"]
        fsts = np.array([0.6, 0.001, 0.8, 0.95, 0, 0.6, 0.6, 0.1])
        qs = np.array([0.004, 0.0001, 0.008, 0.01, 0.2, 0.004, 0.002, 0.001])
        variants = [Variant(chrom="2", pos=100 + i * 10, variant_id=sv_id,
                            ref="N", alt="<DEL>", filter="PASS", info={}, sv_type="DEL",
                            end=105 + i * 10, length_bp=None) for i, sv_id in enumerate(ids)]
        result = {"fst_max": fsts, "q_value": qs, "p_value": qs.copy(),
                  "fst_max_pair": np.full(len(ids), "A_vs_B"),
                  "pair_names": ["A_vs_B"], "pair_fst": fsts[:, None]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vcf, panel = root / "input.vcf", root / "panel.tsv"
            vcf.write_text("##fileformat=VCFv4.2\n"
                           "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA1\tA2\tB1\tB2\n",
                           encoding="utf-8")
            panel.write_text("sample\tpop\nA1\tA\nA2\tA\nB1\tB\nB2\tB\n", encoding="utf-8")
            output = root / "screening"
            metadata = write_outputs(
                output, variants, np.zeros((len(ids), 4, 2), dtype=np.int8),
                np.array(["A", "A", "B", "B"]), ["A", "B"], result,
                vcf=vcf, panel=panel, region="all", genome_build="GRCh38",
                permutations=1000, seed=42, fdr_threshold=0.01, top_k=3, skipped={},
            )
            with (output / "ranking.tsv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual([row["sv_id"] for row in rows],
                             ["bad_q", "fst_first", "lower_q", "q_tie_a", "q_tie_b", "low", "below_mean", "zero"])
            self.assertEqual([int(row["candidate_rank"]) for row in rows], list(range(1, 9)))
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([case["case_id"] for case in manifest["cases"]],
                             ["fst_first", "lower_q", "q_tie_a"])
            self.assertEqual({path.stem for path in (output / "candidates").glob("*.json")},
                             {"fst_first", "lower_q", "q_tie_a"})
            expected_order = "maximum Fst descending, BH q-value ascending, then SV ID ascending"
            self.assertEqual(metadata["candidate_sort_order"], expected_order)
            self.assertEqual(metadata["top_k"], 3)
            self.assertEqual(metadata["significant_variant_count"], 4)
            self.assertEqual(metadata["emitted_candidate_count"], 3)
            self.assertEqual(json.loads((output / "screening_metadata.json").read_text(encoding="utf-8")), metadata)
            for rank, case in enumerate(manifest["cases"], start=2):
                candidate = json.loads((output / case["input"]).read_text(encoding="utf-8"))
                self.assertEqual(candidate["statistics"]["candidate_rank"], rank)
                context = candidate["statistical_context"]
                self.assertIn(expected_order, context)
                self.assertIn("Top-k candidates are selected from SVs passing both thresholds", context)
                self.assertIn("candidate ranks can have gaps after filtering", context)
                self.assertNotIn("BH q-value ascending, maximum Fst descending", context)

    def test_hudson_fst_known_biallelic_example(self) -> None:
        result = hudson_fst(
            np.array([1]), np.array([4]), np.array([3]), np.array([4])
        )
        self.assertAlmostEqual(float(result[0]), 0.2)

    def test_bh_fdr(self) -> None:
        np.testing.assert_allclose(
            bh_fdr(np.array([0.01, 0.02, 0.04])),
            np.array([0.03, 0.03, 0.04]),
        )

    def test_invalid_genotypes_are_counted_without_aborting_vcf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vcf = Path(temporary) / "small.vcf"
            header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA1\tA2\tB1\tB2\n"
            rows = [
                "2\t110\tbad_token\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END=150\tGT\t0/x\t0/0\t1/1\t1/1\n",
                "2\t120\tshort_row\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END=150\tGT\t0/0\n",
                "2\t130\tvalid\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END=150\tGT\t0/0\t0/0\t1/1\t1/1\n",
            ]
            vcf.write_text(header + "".join(rows), encoding="utf-8")
            variants, genotypes, labels, skipped = read_vcf_region(
                vcf, {"A1": "A", "A2": "A", "B1": "B", "B2": "B"}, parse_region("all")
            )
            self.assertEqual([variant.variant_id for variant in variants], ["valid"])
            self.assertEqual(skipped["invalid_gt"], 2)
            self.assertEqual(genotypes.shape, (1, 4, 2))
            self.assertEqual(labels.tolist(), ["A", "A", "B", "B"])

    def test_region_vcf_and_permutation_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            panel = root / "panel.tsv"
            panel.write_text(
                "sample\tpop\nA1\tA\nA2\tA\nB1\tB\nB2\tB\nC1\tC\nC2\tC\n",
                encoding="utf-8",
            )
            vcf = root / "small.vcf.gz"
            body = (
                "##fileformat=VCFv4.2\n"
                '##INFO=<ID=MC,Number=.,Type=String,Description="Merged calls.">\n'
                '##INFO=<ID=NS,Number=1,Type=Integer,Description="Header-specific sample count, not carrier count">\n'
                '##INFO=<ID=END,Number=1,Type=Integer,Description="">\n'
                '##INFO=<ID=UNUSED,Number=1,Type=String,Description="Unused definition">\n'
                "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA1\tA2\tB1\tB2\tC1\tC2\n"
                "2\t110\tv1\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END=150;MC=source_call;NS=6\tGT\t0/0\t0/0\t1/1\t1/1\t0/1\t0/1\n"
                "2\t180\tv2\tN\t<DUP>\t.\tPASS\tSVTYPE=DUP;END=220\tGT\t0/1\t0/1\t0/1\t0/1\t0/1\t0/1\n"
                "2\t190\tmulti\tN\t<DEL>,<DUP>\t.\tPASS\tSVTYPE=CNV;END=230\tGT\t0/1\t0/1\t0/1\t0/1\t0/1\t0/1\n"
                "3\t110\tv3\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END=150\tGT\t0/0\t0/0\t1/1\t1/1\t0/1\t0/1\n"
                "X\t110\tvx\tN\t<DEL>\t.\tPASS\tSVTYPE=DEL;END=150\tGT\t0/0\t0/0\t1/1\t1/1\t0/1\t0/1\n"
            )
            with gzip.open(vcf, "wt", encoding="utf-8") as handle:
                handle.write(body)

            populations = ["A", "B", "C"]
            mapping = load_panel(panel, populations)
            variants, genotypes, labels, skipped = read_vcf_region(
                vcf, mapping, parse_region("chr2:100-250")
            )
            self.assertEqual([variant.variant_id for variant in variants], ["v1", "v2"])
            self.assertEqual(skipped["multiallelic"], 1)
            first = calculate(genotypes, labels, populations, permutations=49, seed=7)
            second = calculate(genotypes, labels, populations, permutations=49, seed=7)
            np.testing.assert_array_equal(first["p_value"], second["p_value"])
            np.testing.assert_array_equal(first["exceedances"], np.array([9, 49]))
            self.assertEqual(first["fst_max_pair"][0], "A_vs_B")
            self.assertGreater(first["fst_max"][0], first["fst_max"][1])

            first["q_value"][0] = 0.001
            output = root / "screening"
            write_outputs(
                output, variants, genotypes, labels, populations, first,
                vcf=vcf, panel=panel, region="chr2:100-250", genome_build="GRCh38",
                permutations=49, seed=7, fdr_threshold=0.01, top_k=1, skipped=skipped,
            )
            candidate = json.loads((output / "candidates" / "v1.json").read_text())
            self.assertEqual(candidate["source_record"]["info_definition"], {
                "MC": "Merged calls.", "NS": "Header-specific sample count, not carrier count",
            })
            normalized = normalize_sv_input(json.dumps(candidate))
            self.assertEqual(normalized["source_record"]["INFO"], candidate["source_record"]["INFO"])
            self.assertEqual(normalized["source_record"]["info_definition"]["NS"], {
                "description": "Header-specific sample count, not carrier count", "source": "provided",
            })
            self.assertEqual(normalized["source_record"]["info_definition"]["END"]["source"], "1000g_dictionary")
            context = candidate["statistical_context"]
            self.assertEqual(candidate["statistics"]["candidate_rank"], 1)
            self.assertNotIn("rank", candidate["statistics"])
            self.assertEqual((output / "ranking.tsv").read_text().split("\t", 1)[0], "candidate_rank")
            self.assertIn("not the p-value rank used internally in BH correction", context)
            self.assertIn("More than two populations", context)
            two_group_context = build_statistical_context(
                ["A", "B"], {"A": 2, "B": 2}, permutations=49, seed=7,
                variant_count=2, region="all", fdr_threshold=0.01, mean_fst=0.1,
            )
            self.assertIn("Exactly two populations", two_group_context)
            self.assertIn("fst_max_pair names that sole comparison", two_group_context)
            for text in ("A (n=2)", "B (n=2)", "C (n=2)", "49 times", "seed 7", "all 2 analyzed SVs"):
                self.assertIn(text, context)
            for field in ("permutation_seed", "permutations", "fst_method", "selection_rule", "mean_fst_threshold"):
                self.assertNotIn(field, candidate["statistics"])
            self.assertEqual(normalize_sv_input(json.dumps(candidate))["statistical_context"], context)
            invalid = {**candidate, "statistical_context": {"seed": 7}}
            self.assertEqual(normalize_sv_input(json.dumps(invalid))["status"], "validation_error")

            all_variants, _, _, all_skipped = read_vcf_region(vcf, mapping, parse_region("all"))
            self.assertEqual([variant.variant_id for variant in all_variants], ["v1", "v2", "v3"])
            self.assertEqual(all_skipped["outside_region"], 1)


if __name__ == "__main__":
    unittest.main()
