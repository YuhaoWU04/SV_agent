"""Runtime configuration for the SV investigation workflow."""

from __future__ import annotations

import os

from . import __version__


MODEL = os.getenv("SV_AGENT_MODEL", "gemini-3.5-flash")
MODEL_BACKEND = os.getenv("SV_AGENT_MODEL_BACKEND", "gemini")
MODEL_API_BASE = os.getenv("SV_AGENT_API_BASE", "") if MODEL_BACKEND == "litellm" else ""

# One list for baseline query provenance, operational metrics and collection tests.
# Keys remain stable in saved metrics; values are the tool-owned state keys.
BASELINE_SOURCE_KEYS = {
    "ensembl_overlap": "region_annotation",
    "ensembl_vep": "vep_evidence",
    "gnomad_sv": "database_evidence",
    "clingen_dosage": "clingen_dosage_evidence",
    "clinvar": "clinvar_evidence",
    "dbvar": "dbvar_evidence",
    "dgv": "dgv_evidence",
    "regulatory_elements": "regulatory_element_evidence",
    "regulatory_gene_links": "regulatory_gene_link_evidence",
    "molecular_qtl": "qtl_evidence",
    "mappability": "mappability_evidence",
}


def build_model():
    """Keep Gemini native; opt into ADK's optional LiteLLM adapter."""
    if MODEL_BACKEND == "gemini":
        return MODEL
    if MODEL_BACKEND != "litellm":
        raise ValueError("SV_AGENT_MODEL_BACKEND must be gemini or litellm")
    if not MODEL_API_BASE or "/" not in MODEL:
        raise ValueError(
            "LiteLLM requires SV_AGENT_API_BASE and a provider-prefixed "
            "SV_AGENT_MODEL (e.g. openai/local-model or ollama_chat/qwen3:0.6b)"
        )
    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as exc:
        raise ImportError(
            "Local models require the optional dependency: pip install -e '.[local]'"
        ) from exc
    return LiteLlm(
        model=MODEL,
        api_base=MODEL_API_BASE,
        api_key=os.getenv("SV_AGENT_API_KEY", "local"),
    )


# General APIs use the shared timeout. Ensembl has separate controls because its
# endpoints have shown intermittent latency and server-side failures.
HTTP_TIMEOUT_SECONDS = max(1.0, float(os.getenv("SV_AGENT_HTTP_TIMEOUT", "20")))
ENSEMBL_HTTP_TIMEOUT_SECONDS = max(
    1.0, float(os.getenv("SV_AGENT_ENSEMBL_HTTP_TIMEOUT", "60"))
)
ENSEMBL_MAX_ATTEMPTS = max(1, int(os.getenv("SV_AGENT_ENSEMBL_MAX_ATTEMPTS", "4")))
ENSEMBL_RETRY_BACKOFF_SECONDS = max(
    0.0, float(os.getenv("SV_AGENT_ENSEMBL_RETRY_BACKOFF", "5"))
)
MAX_DATABASE_RECORDS = max(1, int(os.getenv("SV_AGENT_MAX_DATABASE_RECORDS", "10")))
MAX_VEP_INTERVAL_BP = max(
    1, int(os.getenv("SV_AGENT_MAX_VEP_INTERVAL_BP", "5000000"))
)
MAX_PUBMED_RECORDS = max(1, int(os.getenv("SV_AGENT_MAX_PUBMED_RECORDS", "5")))
MAX_PUBMED_QUERIES = 3
DEFAULT_BREAKPOINT_TOLERANCE_BP = max(
    0, int(os.getenv("SV_AGENT_BREAKPOINT_TOLERANCE_BP", "500"))
)
# This is a safety boundary, not a prompt preference.  The adaptive investigator
# cannot exceed it even if the model asks for more calls.
MAX_ADAPTIVE_QUERIES = 2
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")

USER_AGENT = os.getenv(
    "SV_AGENT_USER_AGENT",
    f"sv-investigator/{__version__} (academic research; configure NCBI_EMAIL)",
)
