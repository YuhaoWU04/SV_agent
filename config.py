"""Runtime configuration for the SV investigation workflow."""

from __future__ import annotations

import os


MODEL = os.getenv("SV_AGENT_MODEL", "gemini-3.5-flash")

# General APIs use the shared timeout. Ensembl has separate controls because its
# overlap endpoint is queried concurrently and has shown intermittent latency.
HTTP_TIMEOUT_SECONDS = float(os.getenv("SV_AGENT_HTTP_TIMEOUT", "20"))
ENSEMBL_HTTP_TIMEOUT_SECONDS = float(os.getenv("SV_AGENT_ENSEMBL_HTTP_TIMEOUT", "30"))
ENSEMBL_MAX_ATTEMPTS = max(1, int(os.getenv("SV_AGENT_ENSEMBL_MAX_ATTEMPTS", "2")))
ENSEMBL_MAX_CONCURRENT_REQUESTS = max(
    1, int(os.getenv("SV_AGENT_ENSEMBL_MAX_CONCURRENT_REQUESTS", "4"))
)
ENSEMBL_RETRY_BACKOFF_SECONDS = max(
    0.0, float(os.getenv("SV_AGENT_ENSEMBL_RETRY_BACKOFF", "1"))
)
MAX_DATABASE_RECORDS = int(os.getenv("SV_AGENT_MAX_DATABASE_RECORDS", "10"))
MAX_PUBMED_RECORDS = int(os.getenv("SV_AGENT_MAX_PUBMED_RECORDS", "5"))
MAX_PUBMED_QUERIES = 3
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
