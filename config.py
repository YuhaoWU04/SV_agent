"""Runtime configuration for the SV investigation workflow."""

from __future__ import annotations

import os


MODEL = os.getenv("SV_AGENT_MODEL", "gemini-3.5-flash")
HTTP_TIMEOUT_SECONDS = float(os.getenv("SV_AGENT_HTTP_TIMEOUT", "20"))
MAX_DATABASE_RECORDS = int(os.getenv("SV_AGENT_MAX_DATABASE_RECORDS", "10"))
MAX_PUBMED_RECORDS = int(os.getenv("SV_AGENT_MAX_PUBMED_RECORDS", "8"))
DEFAULT_BREAKPOINT_TOLERANCE_BP = int(
    os.getenv("SV_AGENT_BREAKPOINT_TOLERANCE_BP", "500")
)
# This is a safety boundary, not a prompt preference.  The adaptive investigator
# cannot exceed it even if the model asks for more calls.
MAX_ADAPTIVE_QUERIES = 2
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")

USER_AGENT = os.getenv(
    "SV_AGENT_USER_AGENT",
    "sv-investigator/0.1 (academic research; configure NCBI_EMAIL)",
)
