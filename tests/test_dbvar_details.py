import unittest
from unittest.mock import patch

from sv_investigator.tools import _query_dbvar_details
from sv_investigator.state_pipeline import _catalog_record


def table(headers, rows):
    return "<table><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>" + "".join(
        "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in rows
    ) + "</table>"


class DbvarDetailTests(unittest.TestCase):
    def test_call_types_coordinates_and_numeric_cn_are_separate(self):
        for sv_type, submitted_type, hgvs in (
            ("DEL", "deletion", "NC_000003.12:g.101_158del"),
            ("DUP", "duplication", "NC_000003.12:g.101_158dup"),
            ("INV", "inversion", "NC_000003.12:g.101_158inv"),
            ("INS", "insertion", "NC_000003.12:g.101_102insAC"),
        ):
            with self.subTest(sv_type=sv_type):
                page = table(
                    ["Variant Call ID", "Type", "Sample ID", "Zygosity", "Method", "Inserted Sequence"],
                    [["nssv1", submitted_type, "sample1", "Heterozygous", "Sequencing", "AC"]],
                ) + table(
                    ["Variant Call ID", "Assembly", "Chr", "Start", "Stop", "HGVS", "Orientation"],
                    [["nssv1", "GRCh37", "Chr3", "1", "58", "wrong-build", "+"],
                     ["nssv1", "GRCh38", "Chr3", "101", "158", hgvs, "-"]],
                )
                sv = {"genome_build": "GRCh38", "chrom": "3", "start": 101, "end": 158, "sv_type": sv_type}
                with patch("sv_investigator.tools._text_request", return_value=(page, None)):
                    result = _query_dbvar_details("https://example.test/nsv1", sv, 10)
                call = result["calls"][0]
                self.assertEqual(call["variant_type"], submitted_type)
                self.assertEqual(call["type_compatibility"], "compatible")
                self.assertEqual(call["zygosity"], "Heterozygous")
                self.assertEqual(call["placements"][0]["hgvs"], hgvs)
                self.assertEqual(len(call["placements"]), 1)
                self.assertNotIn("reported_copy_numbers", result)
                self.assertNotIn("copy_number_status", result)
                self.assertEqual(call["additional_fields"]["Inserted Sequence"], "AC")
                self.assertEqual(call["placements"][0]["additional_fields"]["Orientation"], "-")
                self.assertEqual(result["additional_details"][0]["submitted_fields"]["Assembly"], "GRCh37")

    def test_explicit_cn_and_missing_or_invalid_detail_pages(self):
        sv = {"genome_build": "GRCh38", "chrom": "3", "start": 101, "end": 158, "sv_type": "CNV"}
        page = table(["Variant Call ID", "Type", "Copy Number"], [["nssv1", "copy number gain", "3"]])
        page += table(["Sample ID", "CN"], [["S2", "0"], ["S3", "NaN"], ["S4", "-1"], ["S5", "unknown"]])
        page += '<a href="https://ftp.ncbi.nlm.nih.gov/pub/dbVar/data/Homo_sapiens/by_study/genotype/nstd1">FTP site</a>'
        with patch("sv_investigator.tools._text_request", return_value=(page, None)):
            result = _query_dbvar_details("https://example.test/nsv1", sv, 10)
        self.assertEqual([x["value"] for x in result["reported_copy_numbers"]], [3, 0])
        self.assertEqual(result["reported_copy_numbers"][1]["sample_id"], "S2")
        self.assertNotIn("copy_number_status", result)
        self.assertEqual(len(result["genotype_download_links"]), 1)
        self.assertEqual(len(result["unparsed_copy_numbers"]), 3)
        record = {"record_id": "nsv1", "call_details": result}
        catalog = _catalog_record("DBV-BL-001", {"record": record, "context": {}}, [])
        self.assertEqual(catalog["key_facts"]["call_details"], result)
        with patch("sv_investigator.tools._text_request", return_value=("<html>Changed page</html>", None)):
            result = _query_dbvar_details("https://example.test/nsv1", sv, 10)
        self.assertEqual(result["status"], "unavailable")
        with patch("sv_investigator.tools._text_request", return_value=(None, "TimeoutError")):
            result = _query_dbvar_details("https://example.test/nsv1", sv, 10)
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
