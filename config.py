"""Runtime configuration for the SV investigation workflow."""

from __future__ import annotations

import os


MODEL = os.getenv("SV_AGENT_MODEL", "gemini-3.5-flash")
HTTP_TIMEOUT_SECONDS = float(os.getenv("SV_AGENT_HTTP_TIMEOUT", "20"))
MAX_DATABASE_RECORDS = int(os.getenv("SV_AGENT_MAX_DATABASE_RECORDS", "10"))
MAX_PUBMED_RECORDS = int(os.getenv("SV_AGENT_MAX_PUBMED_RECORDS", "8"))
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
OMIM_API_KEY = os.getenv("OMIM_API_KEY", "")

USER_AGENT = os.getenv(
    "SV_AGENT_USER_AGENT",
    "sv-investigator/0.1 (academic research; configure NCBI_EMAIL)",
)
