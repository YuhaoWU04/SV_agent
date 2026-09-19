import importlib.util
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts" / "generate_flow_diagram.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_flow_diagram", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ArchitectureDocumentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()
        cls.data = cls.generator.load_manifest()

    def test_manifest_is_internally_consistent(self):
        self.assertEqual(self.generator.validate_manifest(self.data), [])

    def test_generated_documents_are_current(self):
        fingerprint = self.generator.source_fingerprint()
        expected = {
            self.generator.HTML_PATH: self.generator.render_html(self.data, fingerprint),
            self.generator.DICTIONARY_PATH: self.generator.render_dictionary(
                self.data, fingerprint
            ),
        }
        for path, content in expected.items():
            with self.subTest(path=path.name):
                self.assertTrue(path.exists())
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_canvas_contains_all_stages_and_interactions(self):
        html = self.generator.HTML_PATH.read_text(encoding="utf-8")
        for stage in self.data["stages"]:
            self.assertIn(stage["title"], html)
        for control_id in (
            "search", "zoomIn", "zoomOut", "fit", "reset", "traceAll", "showAll"
        ):
            self.assertIn(f'id="{control_id}"', html)
        self.assertIn("function portOf(element, side)", html)
        self.assertIn("function focusedEdges()", html)
        self.assertNotIn("stage-edge", html)


if __name__ == "__main__":
    unittest.main()
