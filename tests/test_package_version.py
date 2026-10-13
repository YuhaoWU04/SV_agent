import json
import tomllib
import unittest
from pathlib import Path

from sv_investigator import __version__
from sv_investigator.schemas import SVReport


class PackageVersionTest(unittest.TestCase):
    def test_release_versions_are_consistent(self):
        root = Path(__file__).resolve().parents[1]
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        lineage = json.loads((root / "architecture/data_lineage.json").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["version"], __version__)
        self.assertEqual(lineage["metadata"]["version"], __version__)
        self.assertEqual(SVReport.model_fields["report_version"].default, __version__)
