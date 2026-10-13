import builtins
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from sv_investigator import config


class ModelBackendTest(unittest.TestCase):
    def test_gemini_does_not_import_optional_adapter(self):
        original_import = builtins.__import__

        def reject_adapter(name, *args, **kwargs):
            if name == "google.adk.models.lite_llm":
                raise AssertionError("Gemini must not import LiteLLM")
            return original_import(name, *args, **kwargs)

        with patch.object(config, "MODEL_BACKEND", "gemini"), patch(
            "builtins.__import__", side_effect=reject_adapter
        ):
            self.assertEqual(config.build_model(), config.MODEL)

    def test_local_configuration_and_invalid_backend(self):
        adapter = Mock()
        with patch.multiple(
            config, MODEL_BACKEND="litellm", MODEL="openai/qwen3-0.6b",
            MODEL_API_BASE="http://127.0.0.1:8080/v1",
        ), patch.dict("os.environ", {"SV_AGENT_API_KEY": "test-key"}), patch.dict(
            "sys.modules", {"google.adk.models.lite_llm": SimpleNamespace(LiteLlm=adapter)}
        ):
            self.assertIs(config.build_model(), adapter.return_value)
            adapter.assert_called_once_with(
                model="openai/qwen3-0.6b",
                api_base="http://127.0.0.1:8080/v1", api_key="test-key",
            )
            with patch.object(config, "MODEL_API_BASE", ""):
                with self.assertRaises(ValueError):
                    config.build_model()
        with patch.object(config, "MODEL_BACKEND", "typo"):
            with self.assertRaises(ValueError):
                config.build_model()

    def test_missing_local_dependency_has_install_hint(self):
        original_import = builtins.__import__

        def missing_adapter(name, *args, **kwargs):
            if name == "google.adk.models.lite_llm":
                raise ImportError("missing litellm")
            return original_import(name, *args, **kwargs)

        with patch.multiple(
            config, MODEL_BACKEND="litellm", MODEL="openai/local-model",
            MODEL_API_BASE="http://127.0.0.1:8080/v1",
        ), patch("builtins.__import__", side_effect=missing_adapter):
            with self.assertRaisesRegex(ImportError, r"\[local\]"):
                config.build_model()


if __name__ == "__main__":
    unittest.main()
