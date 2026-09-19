"""Deterministic validation and public database adapters.

All functions return JSON-compatible dictionaries. A database failure is data:
it is represented by an explicit status and does not masquerade as no evidence.
"""

from __future__ import annotations

import copy
import csv
import io
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, MutableMapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .config import (
    DEFAULT_BREAKPOINT_TOLERANCE_BP,
    ENSEMBL_HTTP_TIMEOUT_SECONDS,
    ENSEMBL_MAX_ATTEMPTS,
    ENSEMBL_MAX_CONCURRENT_REQUESTS,
    ENSEMBL_RETRY_BACKOFF_SECONDS,
    HTTP_TIMEOUT_SECONDS,
    MAX_ADAPTIVE_QUERIES,
    MAX_DATABASE_RECORDS,
    MAX_PUBMED_RECORDS,
    MAX_VEP_INTERVAL_BP,
    NCBI_API_KEY,
    NCBI_EMAIL,
    USER_AGENT,
)


ENSEMBL_REST = "https://rest.ensembl.org"
# Several baseline scopes are executed in parallel. This process-wide gate prevents
# simultaneous investigations from multiplying the load sent to Ensembl.
_ENSEMBL_REQUEST_SLOTS = threading.BoundedSemaphore(ENSEMBL_MAX_CONCURRENT_REQUESTS)
_ENSEMBL_RETRYABLE_ERRORS = {
    "TimeoutError", "URLError", "HTTP 429", "HTTP 500", "HTTP 502",
    "HTTP 503", "HTTP 504",
}
# Tool calls emitted together by a model may run concurrently. Reserve adaptive
# budget under a short lock; external requests themselves run outside this lock.
_ADAPTIVE_STATE_LOCK = threading.Lock()
# NCBI permits a lower request rate without an API key. Serialize E-utilities calls
# across ClinVar, dbVar, and PubMed so concurrent baseline tasks remain polite.
_NCBI_REQUEST_LOCK = threading.Lock()
_NCBI_LAST_REQUEST_MONOTONIC = 0.0
GNOMAD_GRAPHQL = "https://gnomad.broadinstitute.org/api"
NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CLINGEN_DOSAGE_CSV = "https://search.clinicalgenome.org/kb/gene-dosage/downloadall"
UCSC_API = "https://api.genome.ucsc.edu"
SUPPORTED_BUILDS = {"GRCh37", "GRCh38"}
SUPPORTED_TYPES = {"DEL", "DUP", "INV", "INS", "BND", "CNV"}
COORDINATE_SYSTEM = "1-based-inclusive"
ADAPTIVE_ACTIONS = {
    "QUERY_NEAREST_GENE_10KB",
    "QUERY_NEAREST_GENE_50KB",
    "QUERY_TRANSCRIPTS",
    "QUERY_EXONS",
    "ANNOTATE_BND_MATE_TRANSCRIPTS",
    "EXPAND_GNOMAD_RETRIEVAL_2KB",
    "EXPAND_GNOMAD_RETRIEVAL_10KB",
}

# Primary chromosome lengths from the Genome Reference Consortium assembly
# pages. Patch releases do not change these assembled chromosome coordinates.
CHROMOSOME_LENGTHS: dict[str, dict[str, int]] = {
    "GRCh37": {
        "1": 249250621, "2": 243199373, "3": 198022430,
        "4": 191154276, "5": 180915260, "6": 171115067,
        "7": 159138663, "8": 146364022, "9": 141213431,
        "10": 135534747, "11": 135006516, "12": 133851895,
        "13": 115169878, "14": 107349540, "15": 102531392,
        "16": 90354753, "17": 81195210, "18": 78077248,
        "19": 59128983, "20": 63025520, "21": 48129895,
        "22": 51304566, "X": 155270560, "Y": 59373566,
        "MT": 16569,
    },
    "GRCh38": {
        "1": 248956422, "2": 242193529, "3": 198295559,
        "4": 190214555, "5": 181538259, "6": 170805979,
        "7": 159345973, "8": 145138636, "9": 138394717,
        "10": 133797422, "11": 135086622, "12": 133275309,
        "13": 114364328, "14": 107043718, "15": 101991189,
        "16": 90338345, "17": 83257441, "18": 80373285,
        "19": 58617616, "20": 64444167, "21": 46709983,
        "22": 50818468, "X": 156040895, "Y": 57227415,
        "MT": 16569,
    },
}

SV_TYPE_ALIASES = {
    "DEL": "DEL", "DELETION": "DEL", "LOSS": "DEL", "CN0": "DEL",
    "DUP": "DUP", "DUPLICATION": "DUP", "GAIN": "DUP",
    "INV": "INV", "INVERSION": "INV",
    "INS": "INS", "INSERTION": "INS", "MEI": "INS",
    "MOBILE_ELEMENT_INSERTION": "INS", "ALU": "INS", "SVA": "INS",
    "ALU_INSERTION": "INS", "SVA_INSERTION": "INS",
    "LINE": "INS", "LINE1": "INS", "LINE_1": "INS", "L1": "INS",
    "LINE_INSERTION": "INS", "LINE1_INSERTION": "INS",
    "LINE_1_INSERTION": "INS", "L1_INSERTION": "INS",
    "BND": "BND", "BREAKEND": "BND", "TRA": "BND",
    "TRANSLOCATION": "BND", "CTX": "BND",
    "CNV": "CNV", "COPY_NUMBER_VARIANT": "CNV",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_json_loads(value: str, field_name: str) -> dict[str, Any]:
    if not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must contain a JSON object")
    return parsed


def _json_request(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    *,
    timeout_seconds: float | None = None,
) -> tuple[Any | None, str | None]:
    query = f"?{urlencode(params, doseq=True)}" if params else ""
    request_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = Request(f"{url}{query}", headers=request_headers)
    try:
        timeout = HTTP_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), None
    except HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (URLError, TimeoutError) as exc:
        return None, type(exc).__name__
    except json.JSONDecodeError:
        return None, "invalid_json_response"


def _text_request(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    *,
    timeout_seconds: float | None = None,
) -> tuple[str | None, str | None]:
    """Fetch a public text resource while preserving failure as explicit data."""
    query = f"?{urlencode(params, doseq=True)}" if params else ""
    request_headers = {"Accept": "text/plain,text/csv,*/*", "User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = Request(f"{url}{query}", headers=request_headers)
    try:
        timeout = HTTP_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8-sig"), None
    except HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (URLError, TimeoutError) as exc:
        return None, type(exc).__name__
    except UnicodeDecodeError:
        return None, "invalid_text_encoding"


def _ensembl_json_request(
    url: str, params: dict[str, Any]
) -> tuple[Any | None, str | None, int]:
    """Retry transient Ensembl failures and return the number of attempts used."""
    for attempt in range(1, ENSEMBL_MAX_ATTEMPTS + 1):
        with _ENSEMBL_REQUEST_SLOTS:
            payload, error = _json_request(
                url, params, {"Content-Type": "application/json"},
                timeout_seconds=ENSEMBL_HTTP_TIMEOUT_SECONDS,
            )
        if error not in _ENSEMBL_RETRYABLE_ERRORS or attempt == ENSEMBL_MAX_ATTEMPTS:
            return payload, error, attempt
        # Wait outside the semaphore so another request can use the released slot.
        if ENSEMBL_RETRY_BACKOFF_SECONDS:
            time.sleep(ENSEMBL_RETRY_BACKOFF_SECONDS * attempt)
    raise AssertionError("unreachable")


def _ensembl_overlap_request(
    host: str, chrom: str, interval: list[int], feature: str
) -> tuple[Any | None, str | None, int, str]:
    """Build one overlap request consistently for baseline and adaptive queries."""
    region = quote(f"{chrom}:{interval[0]}-{interval[1]}", safe=":-")
    endpoint = f"{host}/overlap/region/human/{region}"
    payload, error, attempts = _ensembl_json_request(
        endpoint, {"feature": feature}
    )
    return payload, error, attempts, f"{endpoint}?feature={feature}"


def _json_post(url: str, payload: dict[str, Any]) -> tuple[Any | None, str | None]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8")), None
    except HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (URLError, TimeoutError) as exc:
        return None, type(exc).__name__
    except json.JSONDecodeError:
        return None, "invalid_json_response"


def _clean_chrom(value: Any) -> str:
    chrom = str(value).strip()
    chrom = re.sub(r"^chr", "", chrom, flags=re.IGNORECASE)
    if chrom.upper() == "M":
        chrom = "MT"
    if not re.fullmatch(r"(?:[1-9]|1[0-9]|2[0-2]|X|Y|MT)", chrom, re.IGNORECASE):
        raise ValueError("chrom must be 1-22, X, Y, or MT")
    return chrom.upper()


def _normalize_genome_build(value: Any) -> str:
    if value is None or isinstance(value, bool):
        raise ValueError("genome_build must identify GRCh37/hg19 or GRCh38/hg38")
    token = re.sub(r"[\s_.-]", "", str(value)).lower()
    if token in {"37", "b37", "build37", "humanbuild37", "hg19"} or re.fullmatch(
        r"grch37(?:p\d+)?", token
    ):
        return "GRCh37"
    if token in {"38", "b38", "build38", "humanbuild38", "hg38"} or re.fullmatch(
        r"grch38(?:p\d+)?", token
    ):
        return "GRCh38"
    raise ValueError(
        f"unsupported genome_build {value!r}; expected GRCh37/hg19 or GRCh38/hg38"
    )


def _parse_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer, not a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        return int(value.strip())
    raise ValueError(f"{field_name} must be an integer")


def _get_vcf_field(payload: dict[str, Any], *names: str) -> Any:
    """Read a field from the JSON object or a nested source_record INFO object."""
    for container in (
        payload,
        payload.get("source_record"),
        (payload.get("source_record") or {}).get("INFO")
        if isinstance(payload.get("source_record"), dict) else None,
        (payload.get("source_record") or {}).get("info")
        if isinstance(payload.get("source_record"), dict) else None,
    ):
        if not isinstance(container, dict):
            continue
        for name in names:
            if name in container:
                return container[name]
    return None


def _parse_confidence_offsets(value: Any, field_name: str) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, str):
        values: Any = [part.strip() for part in value.split(",")]
    else:
        values = value
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        raise ValueError(f"{field_name} must contain exactly two integer offsets")
    lower = _parse_integer(values[0], f"{field_name}[0]")
    upper = _parse_integer(values[1], f"{field_name}[1]")
    if lower > upper:
        raise ValueError(f"{field_name} lower offset must be <= upper offset")
    return [lower, upper]


def _absolute_confidence_interval(
    center: int,
    offsets: list[int] | None,
    chromosome_length: int,
) -> tuple[list[int] | None, bool]:
    if offsets is None:
        return None, False
    unclipped = [center + offsets[0], center + offsets[1]]
    clipped = [max(1, unclipped[0]), min(chromosome_length, unclipped[1])]
    if clipped[0] > clipped[1]:
        raise ValueError("breakpoint confidence interval lies outside the chromosome")
    return clipped, clipped != unclipped


def _parse_flag(value: Any, present: bool = False) -> bool:
    if value is None:
        return present
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() not in {"", "0", "false", "no", "none"}


def _parse_bnd_alt(value: Any) -> dict[str, Any] | None:
    """Parse the remote locus and adjacency orientation from a VCF BND ALT."""
    if value is None or isinstance(value, bool):
        return None
    alt = str(value).strip()
    match = re.search(r"([\[\]])([^:\[\]]+):(\d+)([\[\]])", alt)
    if not match or match.group(1) != match.group(4):
        return None
    mate_chrom = _clean_chrom(match.group(2))
    mate_pos = _parse_integer(match.group(3), "BND ALT mate position")
    return {
        "mate_chrom": mate_chrom,
        "mate_pos": mate_pos,
        "local_orientation": "-" if alt.startswith(("[", "]")) else "+",
        "mate_orientation": "+" if match.group(1) == "[" else "-",
        "alt": alt,
    }


def _optional_bnd_mate(
    payload: dict[str, Any], genome_build: str, warnings: list[str]
) -> dict[str, Any] | None:
    """Read a BND mate without making newly recognized optional fields fatal."""
    alt_value = _get_vcf_field(payload, "alt", "ALT")
    alt_mate: dict[str, Any] | None = None
    if alt_value is not None:
        try:
            alt_mate = _parse_bnd_alt(alt_value)
            if alt_mate is not None and not (
                1 <= alt_mate["mate_pos"]
                <= CHROMOSOME_LENGTHS[genome_build][alt_mate["mate_chrom"]]
            ):
                raise ValueError("BND ALT mate position is outside the chromosome")
        except (ValueError, TypeError):
            warnings.append("BND_ALT_mate_invalid_and_ignored")
            alt_mate = None

    explicit_chrom = _get_vcf_field(payload, "mate_chrom", "chrom2", "CHR2")
    explicit_pos = _get_vcf_field(payload, "mate_pos", "pos2", "POS2")
    # CHR2 + END is a common single-record representation. END alone is not
    # reinterpreted because legacy BND inputs already use end as a local field.
    if explicit_chrom is not None and explicit_pos is None:
        explicit_pos = _get_vcf_field(payload, "END")
        if explicit_pos is None:
            explicit_pos = payload.get("end")

    explicit_mate: dict[str, Any] | None = None
    if explicit_chrom is not None or explicit_pos is not None:
        try:
            if explicit_chrom is None or explicit_pos is None:
                raise ValueError("both mate chromosome and position are required")
            mate_chrom = _clean_chrom(explicit_chrom)
            mate_pos = _parse_integer(explicit_pos, "mate_pos")
            if not 1 <= mate_pos <= CHROMOSOME_LENGTHS[genome_build][mate_chrom]:
                raise ValueError("mate_pos is outside the mate chromosome")
            explicit_mate = {"mate_chrom": mate_chrom, "mate_pos": mate_pos}
        except (ValueError, TypeError):
            warnings.append("explicit_BND_mate_invalid_and_ignored")

    chosen = explicit_mate or alt_mate
    if chosen is None:
        return None
    if alt_mate and explicit_mate and (
        alt_mate["mate_chrom"], alt_mate["mate_pos"]
    ) != (explicit_mate["mate_chrom"], explicit_mate["mate_pos"]):
        warnings.append("BND_ALT_and_explicit_mate_disagree_explicit_mate_used")
    if alt_mate:
        chosen = {
            **chosen,
            "local_orientation": alt_mate["local_orientation"],
            "mate_orientation": alt_mate["mate_orientation"],
            "alt": alt_mate["alt"],
        }
    chosen["source"] = "explicit_fields" if explicit_mate else "vcf_alt"
    return chosen


def _normalize_sv_type(value: Any) -> tuple[str, str | None]:
    if value is None or isinstance(value, bool):
        raise ValueError("sv_type must be a non-empty string")
    original = str(value).strip()
    if not original:
        raise ValueError("sv_type must be a non-empty string")
    token = original.upper().strip("<>").replace("-", "_").replace(" ", "_")
    if token.startswith("INS:ME") or token in {
        "INS:ALU", "INS:LINE", "INS:LINE1", "INS:L1", "INS:SVA"
    }:
        normalized = "INS"
    elif token.startswith("DEL:"):
        normalized = "DEL"
    else:
        normalized = SV_TYPE_ALIASES.get(token, "")
    if normalized not in SUPPORTED_TYPES:
        raise ValueError(f"unsupported sv_type: {original}")

    subtype: str | None = None
    if "ALU" in token:
        subtype = "ALU"
    elif token in {"LINE", "LINE1", "LINE_1", "L1"} or re.search(
        r"(?:LINE[_:]?1|(?:^|[_:])L1(?:$|[_:]))", token
    ):
        subtype = "LINE1"
    elif "SVA" in token:
        subtype = "SVA"
    elif token in {"MEI", "MOBILE_ELEMENT_INSERTION", "INS:ME"}:
        subtype = "MEI"
    return normalized, subtype


def normalize_sv_input(raw_input: str) -> dict[str, Any]:
    """Validate and normalize one candidate structural variant.

    Args:
        raw_input: A JSON object containing genome_build, chrom, start, end,
            sv_type, and optional sv_id, length_bp/SVLEN, statistics, quality,
            and source_record. Coordinates are 1-based and inclusive. Common
            GRCh/hg build names and SV-type aliases are accepted case-insensitively.

    Returns:
        The normalized SV or a validation_error object. Missing optional fields
        are retained as explicit warnings and are never inferred.
    """
    text = raw_input.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        if isinstance(payload.get("sv"), dict):
            payload = {**payload, **payload["sv"]}

        missing = [
            key
            for key in ("genome_build", "chrom", "start", "end", "sv_type")
            if key not in payload
        ]
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        original_build = str(payload["genome_build"]).strip()
        genome_build = _normalize_genome_build(payload["genome_build"])
        chrom = _clean_chrom(payload["chrom"])
        start = _parse_integer(payload["start"], "start")
        end = _parse_integer(payload["end"], "end")
        if start < 1 or end < 1 or start > end:
            raise ValueError(
                "coordinates use 1-based inclusive convention and must satisfy "
                "1 <= start <= end"
            )
        chromosome_length = CHROMOSOME_LENGTHS[genome_build][chrom]
        if start > chromosome_length or end > chromosome_length:
            raise ValueError(
                f"coordinates exceed {genome_build} chromosome {chrom} length "
                f"({chromosome_length} bp)"
            )
        original_sv_type = str(payload["sv_type"]).strip()
        sv_type, sv_subtype = _normalize_sv_type(payload["sv_type"])

        warnings: list[str] = []
        cipos = _parse_confidence_offsets(
            _get_vcf_field(payload, "cipos", "CIPOS"), "CIPOS"
        )
        ciend = _parse_confidence_offsets(
            _get_vcf_field(payload, "ciend", "CIEND"), "CIEND"
        )
        start_confidence_interval, start_ci_clipped = _absolute_confidence_interval(
            start, cipos, chromosome_length
        )
        end_confidence_interval, end_ci_clipped = _absolute_confidence_interval(
            end, ciend, chromosome_length
        )
        if start_ci_clipped:
            warnings.append("CIPOS_clipped_to_chromosome_boundary")
        if end_ci_clipped:
            warnings.append("CIEND_clipped_to_chromosome_boundary")
        uncertainty_status = "complete" if cipos is not None and ciend is not None else (
            "partial" if cipos is not None or ciend is not None else "not_provided"
        )
        imprecise_value = _get_vcf_field(payload, "imprecise", "IMPRECISE")
        source_record = payload.get("source_record")
        imprecise_present = any(
            key in container
            for container in (
                payload,
                source_record if isinstance(source_record, dict) else {},
                source_record.get("INFO", {}) if isinstance(source_record, dict) else {},
                source_record.get("info", {}) if isinstance(source_record, dict) else {},
            )
            for key in ("imprecise", "IMPRECISE")
        )
        imprecise = _parse_flag(imprecise_value, present=imprecise_present)
        if uncertainty_status == "not_provided":
            warnings.append("breakpoint_confidence_intervals_not_provided")
        elif uncertainty_status == "partial":
            warnings.append("breakpoint_confidence_intervals_partially_provided")
        if imprecise and uncertainty_status == "not_provided":
            warnings.append("IMPRECISE_without_CIPOS_or_CIEND")

        bnd_mate = (
            _optional_bnd_mate(payload, genome_build, warnings)
            if sv_type == "BND" else None
        )
        mate_confidence_interval: list[int] | None = None
        if bnd_mate is not None:
            mate_ci_offsets = _parse_confidence_offsets(
                _get_vcf_field(payload, "cimate", "CIMATE"), "CIMATE"
            )
            if mate_ci_offsets is None:
                mate_ci_offsets = ciend
            mate_chromosome_length = CHROMOSOME_LENGTHS[genome_build][bnd_mate["mate_chrom"]]
            mate_confidence_interval, mate_ci_clipped = _absolute_confidence_interval(
                bnd_mate["mate_pos"], mate_ci_offsets, mate_chromosome_length
            )
            if mate_ci_clipped:
                warnings.append(
                    "BND_mate_confidence_interval_clipped_to_chromosome_boundary"
                )
            bnd_mate["confidence_interval"] = mate_confidence_interval
            bnd_mate["confidence_offsets"] = mate_ci_offsets
        elif sv_type == "BND":
            warnings.append("BND_mate_not_provided_first_breakend_only")

        statistics = payload.get("statistics") or {}
        quality = payload.get("quality") or {}
        if not isinstance(statistics, dict) or not isinstance(quality, dict):
            raise ValueError("statistics and quality must be JSON objects")
        if not statistics:
            warnings.append("statistics_not_provided")
        if not quality:
            warnings.append("quality_not_provided")

        normalizations: list[str] = []
        if original_build != genome_build:
            normalizations.append(f"genome_build:{original_build}->{genome_build}")
        original_chrom = str(payload["chrom"]).strip()
        if original_chrom != chrom:
            normalizations.append(f"chrom:{original_chrom}->{chrom}")
        if original_sv_type != sv_type:
            normalizations.append(f"sv_type:{original_sv_type}->{sv_type}")

        interval_length = end - start + 1

        supplied_length = payload.get("length_bp")
        supplied_svlen = payload.get("svlen")
        normalized_supplied_length: int | None = None
        if supplied_length is not None:
            normalized_supplied_length = _parse_integer(supplied_length, "length_bp")
            if normalized_supplied_length <= 0:
                raise ValueError("length_bp must be a positive integer")
        elif supplied_svlen is not None:
            raw_svlen = _parse_integer(supplied_svlen, "svlen")
            if raw_svlen == 0:
                raise ValueError("svlen must be non-zero")
            normalized_supplied_length = abs(raw_svlen)

        if sv_type in {"INS", "BND"}:
            length_bp = normalized_supplied_length
            if sv_type == "INS" and start != end:
                warnings.append("insertion_interval_spans_multiple_reference_bases")
        else:
            length_bp = interval_length
            if normalized_supplied_length is not None and normalized_supplied_length != length_bp:
                warnings.append("provided_length_does_not_match_inclusive_coordinates")

        return {
            "status": "valid",
            "sv_id": str(payload.get("sv_id") or f"{chrom}:{start}-{end}:{sv_type}"),
            "genome_build": genome_build,
            "genome_build_original": original_build,
            "chrom": chrom,
            "start": start,
            "end": end,
            "coordinate_system": COORDINATE_SYSTEM,
            "chromosome_length_bp": chromosome_length,
            "cipos": cipos,
            "ciend": ciend,
            "start_confidence_interval": start_confidence_interval,
            "end_confidence_interval": end_confidence_interval,
            "breakpoint_uncertainty_status": uncertainty_status,
            "imprecise": imprecise,
            "bnd_mate_status": (
                "coordinates_provided" if bnd_mate is not None else
                "not_provided" if sv_type == "BND" else "not_applicable"
            ),
            "mate_chrom": bnd_mate.get("mate_chrom") if bnd_mate else None,
            "mate_pos": bnd_mate.get("mate_pos") if bnd_mate else None,
            "mate_confidence_interval": mate_confidence_interval,
            "local_orientation": bnd_mate.get("local_orientation") if bnd_mate else None,
            "mate_orientation": bnd_mate.get("mate_orientation") if bnd_mate else None,
            "bnd_alt": bnd_mate.get("alt") if bnd_mate else None,
            "bnd_mate_source": bnd_mate.get("source") if bnd_mate else None,
            "breakpoint_fallback_tolerance_bp": DEFAULT_BREAKPOINT_TOLERANCE_BP,
            "breakpoint_fallback_policy": (
                "Used only to retrieve and label nearby candidates when a VCF "
                "confidence interval is absent; it is not a measured confidence interval."
            ),
            "sv_type": sv_type,
            "sv_type_original": original_sv_type,
            "sv_subtype": sv_subtype,
            "length_bp": length_bp,
            "statistics": statistics,
            "quality": quality,
            "source_record": source_record,
            "warnings": warnings,
            "normalizations": normalizations,
        }
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return {"status": "validation_error", "error": str(exc), "raw_input": raw_input}


def _breakpoint_window(
    center: int,
    confidence_interval: list[int] | None,
    chromosome_length: int,
) -> dict[str, Any]:
    if confidence_interval is None:
        return {
            "interval": [
                max(1, center - DEFAULT_BREAKPOINT_TOLERANCE_BP),
                min(chromosome_length, center + DEFAULT_BREAKPOINT_TOLERANCE_BP),
            ],
            "source": "heuristic_fallback",
            "tolerance_bp": DEFAULT_BREAKPOINT_TOLERANCE_BP,
            "is_measured_confidence_interval": False,
        }
    if not isinstance(confidence_interval, (list, tuple)) or len(confidence_interval) != 2:
        raise ValueError("confidence interval must contain two absolute coordinates")
    lower = _parse_integer(confidence_interval[0], "confidence_interval[0]")
    upper = _parse_integer(confidence_interval[1], "confidence_interval[1]")
    if lower < 1 or upper > chromosome_length or lower > upper:
        raise ValueError("confidence interval is outside chromosome bounds or reversed")
    return {
        "interval": [lower, upper],
        "source": "vcf_confidence_interval",
        "tolerance_bp": None,
        "is_measured_confidence_interval": True,
    }


def _query_ensembl_feature_set(
    host: str,
    chrom: str,
    interval: list[int],
) -> dict[str, Any]:
    features: dict[str, Any] = {}
    errors: dict[str, str] = {}
    source_urls: dict[str, str] = {}
    truncated: dict[str, bool] = {}
    attempts_by_feature: dict[str, int] = {}
    feature_names = ("gene", "regulatory", "repeat")

    def fetch(feature: str) -> tuple[str, Any, str | None, int, str]:
        payload, error, attempts, source_url = _ensembl_overlap_request(
            host, chrom, interval, feature
        )
        return feature, payload, error, attempts, source_url

    with ThreadPoolExecutor(max_workers=len(feature_names)) as executor:
        results = list(executor.map(fetch, feature_names))
    for feature, payload, error, attempts, source_url in results:
        attempts_by_feature[feature] = attempts
        source_urls[feature] = source_url
        if error:
            errors[feature] = error
            features[feature] = None
            truncated[feature] = False
        elif not isinstance(payload, list):
            errors[feature] = "invalid_response_shape"
            features[feature] = None
            truncated[feature] = False
        else:
            features[feature] = payload[:MAX_DATABASE_RECORDS]
            truncated[feature] = len(payload) > MAX_DATABASE_RECORDS
    has_successful_query = any(rows is not None for rows in features.values())
    completeness = "complete" if not errors else (
        "partial" if has_successful_query else "failed"
    )
    return {
        "query_region": f"{chrom}:{interval[0]}-{interval[1]}",
        "features": features,
        "errors": errors,
        "truncated": truncated,
        "attempts": attempts_by_feature,
        "source_urls": source_urls,
        "completeness": completeness,
    }


def query_ensembl_region(
    genome_build: str,
    chrom: str,
    start: int,
    end: int,
    sv_type: str,
    start_confidence_interval: list[int] | None = None,
    end_confidence_interval: list[int] | None = None,
    mate_chrom: str | None = None,
    mate_pos: int | None = None,
    mate_confidence_interval: list[int] | None = None,
) -> dict[str, Any]:
    """Query genes, regulatory features, and repeats overlapping an SV interval.

    Args:
        genome_build: GRCh37 or GRCh38.
        chrom: Chromosome without a required chr prefix.
        start: One-based inclusive start coordinate.
        end: One-based inclusive end coordinate.
        sv_type: Canonical DEL, DUP, INV, INS, BND, or CNV label. It is
            retained for provenance; this overlap query is not consequence-aware.
        start_confidence_interval: Optional absolute interval derived from CIPOS.
        end_confidence_interval: Optional absolute interval derived from CIEND.
        mate_chrom: Optional second chromosome for a BND.
        mate_pos: Optional one-based second-breakend position for a BND.
        mate_confidence_interval: Optional absolute interval around mate_pos.

    Returns:
        Evidence records grouped by Ensembl feature type.
    """
    if genome_build not in SUPPORTED_BUILDS:
        return {"source": "Ensembl", "status": "error", "error": "unsupported_build"}
    try:
        chrom = _clean_chrom(chrom)
        start = _parse_integer(start, "start")
        end = _parse_integer(end, "end")
        sv_type, _ = _normalize_sv_type(sv_type)
        chromosome_length = CHROMOSOME_LENGTHS[genome_build][chrom]
        if not 1 <= start <= end <= chromosome_length:
            raise ValueError(
                "coordinates must satisfy 1 <= start <= end <= chromosome length"
            )
        start_window = _breakpoint_window(
            start, start_confidence_interval, chromosome_length
        )
        end_window = _breakpoint_window(
            end, end_confidence_interval, chromosome_length
        )
        mate_window: dict[str, Any] | None = None
        if sv_type == "BND" and mate_chrom is not None and mate_pos is not None:
            mate_chrom = _clean_chrom(mate_chrom)
            mate_pos = _parse_integer(mate_pos, "mate_pos")
            mate_length = CHROMOSOME_LENGTHS[genome_build][mate_chrom]
            if not 1 <= mate_pos <= mate_length:
                raise ValueError("mate_pos is outside the mate chromosome")
            mate_window = _breakpoint_window(
                mate_pos, mate_confidence_interval, mate_length
            )
    except (ValueError, TypeError) as exc:
        return {"source": "Ensembl", "status": "error", "error": str(exc)}
    host = "https://grch37.rest.ensembl.org" if genome_build == "GRCh37" else ENSEMBL_REST
    scopes: dict[str, tuple[str, list[int]]] = {
        "nominal": (chrom, [start, end]),
        "start": (chrom, start_window["interval"]),
    }
    if end_window["interval"] != start_window["interval"]:
        scopes["end"] = (chrom, end_window["interval"])
    if mate_window is not None:
        scopes["mate"] = (mate_chrom, mate_window["interval"])

    # Confidence intervals can make nominal/start/end scopes identical. Query each
    # coordinate interval once, then reuse its immutable result for every role.
    scope_keys = {
        role: (scope_chrom, interval[0], interval[1])
        for role, (scope_chrom, interval) in scopes.items()
    }
    unique_scopes = list(dict.fromkeys(scope_keys.values()))
    with ThreadPoolExecutor(max_workers=len(unique_scopes)) as executor:
        unique_results = dict(zip(
            unique_scopes,
            executor.map(
                lambda item: _query_ensembl_feature_set(
                    host, item[0], [item[1], item[2]]
                ),
                unique_scopes,
            ),
        ))
    scope_results = {
        role: unique_results[scope_key]
        for role, scope_key in scope_keys.items()
    }
    nominal = scope_results["nominal"]
    start_annotation = scope_results["start"]
    if "end" not in scope_results:
        end_annotation = {**start_annotation, "reused_start_breakpoint_query": True}
    else:
        end_annotation = scope_results["end"]
    mate_annotation = scope_results.get("mate")

    completeness_values = {
        nominal["completeness"],
        start_annotation["completeness"],
        end_annotation["completeness"],
    }
    if mate_annotation is not None:
        completeness_values.add(mate_annotation["completeness"])
    completeness = "complete" if completeness_values == {"complete"} else (
        "failed" if completeness_values == {"failed"} else "partial"
    )
    has_records = any(
        rows
        for annotation in (nominal, start_annotation, end_annotation, mate_annotation)
        if annotation is not None
        for rows in annotation["features"].values()
        if rows is not None
    )
    status = "found" if has_records else (
        "not_found" if completeness == "complete" else "error"
    )
    return {
        "source": "Ensembl",
        "status": status,
        "completeness": completeness,
        "genome_build": genome_build,
        "query_region": f"{chrom}:{start}-{end}",
        "sv_type": sv_type,
        "annotation_mode": "spatial_overlap_only",
        "match_type": "region_overlap",
        "features": nominal["features"],
        "errors": nominal["errors"],
        "truncated": nominal["truncated"],
        "attempts": nominal["attempts"],
        "source_urls": nominal["source_urls"],
        "breakpoint_annotations": {
            "start": {**start_window, **start_annotation},
            "end": {**end_window, **end_annotation},
            "mate": (
                {**mate_window, **mate_annotation}
                if mate_window is not None and mate_annotation is not None else None
            ),
        },
        "retrieved_at": _now(),
        "limitations": (
            "Spatial overlap only: sv_type is retained for provenance but does not "
            "change this query. Nominal-interval and breakpoint-window results are "
            "reported separately; a parsed BND mate is also queried separately. "
            "A heuristic breakpoint window retrieves nearby "
            "features but is not a measured confidence interval. Results are capped "
            "per feature type; transcript, "
            "consequence, breakpoint, nearest-gene, and mappability annotation are "
            "not included. A null feature list means that feature query failed."
        ),
    }


_VEP_IMPACT_RANK = {"HIGH": 4, "MODERATE": 3, "LOW": 2, "MODIFIER": 1}


def _compact_vep_consequence(
    row: dict[str, Any], consequence_scope: str
) -> dict[str, Any]:
    """Keep interpretation-relevant VEP fields without copying large responses."""
    common = {
        "consequence_scope": consequence_scope,
        "impact": row.get("impact") or "not_provided",
        "consequence_terms": row.get("consequence_terms") or [],
        "variant_allele": row.get("variant_allele") or "",
        "bp_overlap": row.get("bp_overlap"),
        "percentage_overlap": row.get("percentage_overlap"),
    }
    if consequence_scope == "transcript":
        return {
            **common,
            "record_id": row.get("transcript_id") or row.get("gene_id") or "",
            "gene_id": row.get("gene_id") or "",
            "gene_symbol": row.get("gene_symbol") or "",
            "transcript_id": row.get("transcript_id") or "",
            "biotype": row.get("biotype") or "",
            "canonical": bool(row.get("canonical")),
            "mane_select": row.get("mane_select") or "",
            "mane_plus_clinical": row.get("mane_plus_clinical") or "",
            "exon": row.get("exon") or "",
            "intron": row.get("intron") or "",
            "cds_start": row.get("cds_start"),
            "cds_end": row.get("cds_end"),
            "protein_start": row.get("protein_start"),
            "protein_end": row.get("protein_end"),
            "strand": row.get("strand"),
        }
    identifier_field = {
        "regulatory": "regulatory_feature_id",
        "motif": "motif_feature_id",
        "intergenic": "id",
    }.get(consequence_scope, "id")
    return {
        **common,
        "record_id": row.get(identifier_field) or consequence_scope,
        identifier_field: row.get(identifier_field) or "",
    }


def _vep_overlap_for_sort(row: dict[str, Any]) -> float:
    value = row.get("percentage_overlap")
    if isinstance(value, bool):
        return 0.0
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def query_ensembl_vep(
    normalized_sv_json: str, max_records: int = MAX_DATABASE_RECORDS
) -> dict[str, Any]:
    """Predict compact transcript/regulatory consequences with Ensembl VEP."""
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
        max_records = min(max(1, _parse_integer(max_records, "max_records")), 50)
    except (ValueError, TypeError) as exc:
        return {"source": "Ensembl VEP", "status": "error", "error": str(exc)}

    if sv["sv_type"] in {"BND", "CNV"}:
        return {
            "source": "Ensembl VEP",
            "status": "not_applicable",
            "candidate_sv_type": sv["sv_type"],
            "records": [],
            "reason": (
                "BND adjacency is not represented by the region endpoint."
                if sv["sv_type"] == "BND"
                else "CNV direction is required to choose deletion or duplication."
            ),
            "retrieved_at": _now(),
        }
    interval_length = sv["end"] - sv["start"] + 1
    if interval_length > MAX_VEP_INTERVAL_BP:
        return {
            "source": "Ensembl VEP",
            "status": "not_applicable",
            "candidate_sv_type": sv["sv_type"],
            "records": [],
            "reason": "interval_exceeds_configured_vep_limit",
            "interval_length_bp": interval_length,
            "max_interval_bp": MAX_VEP_INTERVAL_BP,
            "retrieved_at": _now(),
        }

    host = (
        "https://grch37.rest.ensembl.org"
        if sv["genome_build"] == "GRCh37" else ENSEMBL_REST
    )
    region = quote(
        f"{sv['chrom']}:{sv['start']}-{sv['end']}:1", safe=":-"
    )
    endpoint = f"{host}/vep/human/region/{region}/{sv['sv_type']}"
    payload, error, attempts = _ensembl_json_request(
        endpoint, {"canonical": 1, "mane": 1, "numbers": 1}
    )
    source_url = f"{endpoint}?canonical=1;mane=1;numbers=1"
    if error:
        return {
            "source": "Ensembl VEP", "status": "error", "error": error,
            "records": [], "attempts": attempts, "source_url": source_url,
            "retrieved_at": _now(),
        }
    if not isinstance(payload, list):
        return {
            "source": "Ensembl VEP", "status": "error",
            "error": "invalid_response_shape", "records": [],
            "attempts": attempts, "source_url": source_url,
            "retrieved_at": _now(),
        }

    consequence_groups = (
        ("transcript", "transcript_consequences"),
        ("regulatory", "regulatory_feature_consequences"),
        ("motif", "motif_feature_consequences"),
        ("intergenic", "intergenic_consequences"),
    )
    compacted: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    for result in payload:
        if not isinstance(result, dict):
            continue
        inputs.append({
            "id": result.get("id") or "",
            "assembly_name": result.get("assembly_name") or "",
            "chrom": result.get("seq_region_name") or sv["chrom"],
            "start": result.get("start"),
            "end": result.get("end"),
            "allele_string": result.get("allele_string") or "",
            "most_severe_consequence": result.get("most_severe_consequence") or "",
        })
        for scope, field in consequence_groups:
            for row in result.get(field) or []:
                if isinstance(row, dict):
                    compacted.append(_compact_vep_consequence(row, scope))

    compacted.sort(key=lambda row: (
        -_VEP_IMPACT_RANK.get(str(row.get("impact", "")).upper(), 0),
        not bool(row.get("mane_select") or row.get("mane_plus_clinical")),
        not bool(row.get("canonical")),
        -_vep_overlap_for_sort(row),
        str(row.get("record_id") or ""),
    ))
    records = compacted[:max_records]
    for row in records:
        row["source_url"] = source_url
    return {
        "source": "Ensembl VEP",
        "status": "found" if records else "not_found",
        "completeness": "complete",
        "genome_build": sv["genome_build"],
        "candidate_sv_type": sv["sv_type"],
        "query_region": f"{sv['chrom']}:{sv['start']}-{sv['end']}",
        "input_annotations": inputs,
        "records": records,
        "consequence_count": len(compacted),
        "returned_record_count": len(records),
        "records_truncated": len(compacted) > max_records,
        "attempts": attempts,
        "source_url": source_url,
        "retrieved_at": _now(),
        "limitations": (
            "VEP consequences are predictions for the submitted interval and symbolic "
            "allele. They do not establish expression change, dosage pathogenicity, "
            "phenotype, penetrance, or the actual transcript expressed in a sample. "
            "Only a ranked compact subset of consequences is retained."
        ),
    }


def _query_ensembl_single_feature(
    host: str, chrom: str, interval: list[int], feature: str, role: str
) -> dict[str, Any]:
    """Run one explicit Ensembl overlap query for an adaptive action."""
    payload, error, attempts, source_url = _ensembl_overlap_request(
        host, chrom, interval, feature
    )
    query_region = f"{chrom}:{interval[0]}-{interval[1]}"
    response_error = error or (
        None if isinstance(payload, list) else "invalid_response_shape"
    )
    if response_error:
        return {
            "role": role, "query_region": query_region,
            "feature": feature, "status": "error", "records": None,
            "error": response_error, "source_url": source_url,
            "truncated": False, "attempts": attempts,
        }
    records = []
    for index, row in enumerate(payload[:MAX_DATABASE_RECORDS], start=1):
        records.append({
            **row,
            "evidence_id": f"ENS-ADP-{role.upper()}-{feature.upper()}-{index:03d}",
            "feature_type": feature,
            "breakpoint_role": role,
        })
    return {
        "role": role, "query_region": query_region,
        "feature": feature, "status": "found" if records else "not_found",
        "records": records, "error": None, "source_url": source_url,
        "truncated": len(payload) > MAX_DATABASE_RECORDS,
        "attempts": attempts,
    }


def _validated_normalized_sv(normalized_sv_json: str) -> dict[str, Any]:
    """Revalidate identity fields before any stored candidate reaches an API."""
    sv = _safe_json_loads(normalized_sv_json, "normalized_sv_json")
    if sv.get("status") != "valid":
        raise ValueError("normalized SV must have status valid")
    build = _normalize_genome_build(sv.get("genome_build"))
    chrom = _clean_chrom(sv.get("chrom"))
    start = _parse_integer(sv.get("start"), "start")
    end = _parse_integer(sv.get("end"), "end")
    sv_type, _ = _normalize_sv_type(sv.get("sv_type"))
    chromosome_length = CHROMOSOME_LENGTHS[build][chrom]
    if not 1 <= start <= end <= chromosome_length:
        raise ValueError(
            "coordinates must satisfy 1 <= start <= end <= chromosome length"
        )
    return {
        **sv, "genome_build": build, "chrom": chrom, "start": start,
        "end": end, "sv_type": sv_type,
    }


def _ensembl_adaptive_query(sv: dict[str, Any], action: str) -> dict[str, Any]:
    build = sv["genome_build"]
    host = "https://grch37.rest.ensembl.org" if build == "GRCh37" else ENSEMBL_REST
    chrom = sv["chrom"]
    chrom_length = CHROMOSOME_LENGTHS[build][chrom]

    if action.startswith("QUERY_NEAREST_GENE_"):
        padding = 10_000 if action.endswith("10KB") else 50_000
        interval = [
            max(1, sv["start"] - padding),
            min(chrom_length, sv["end"] + padding),
        ]
        result = _query_ensembl_single_feature(
            host, chrom, interval, "gene", "expanded_region"
        )
        for row in result.get("records") or []:
            row_start = row.get("start")
            row_end = row.get("end")
            if isinstance(row_start, int) and isinstance(row_end, int):
                if row_end < sv["start"]:
                    distance = sv["start"] - row_end
                elif row_start > sv["end"]:
                    distance = row_start - sv["end"]
                else:
                    distance = 0
                row["distance_to_nominal_sv_bp"] = distance
        if result.get("records"):
            result["records"].sort(
                key=lambda row: (
                    row.get("distance_to_nominal_sv_bp", 10**18),
                    str(row.get("id", "")),
                )
            )
        return {
            "source": "Ensembl", "action": action, "status": result["status"],
            "retrieval_padding_bp": padding, "results": [result],
            "retrieved_at": _now(),
            "limitations": (
                "Nearest means coordinate distance within the requested search "
                "radius; it does not imply regulation or causality."
            ),
        }

    feature = "transcript" if "TRANSCRIPTS" in action else "exon"
    scopes: list[tuple[str, str, list[int]]] = []
    if action == "ANNOTATE_BND_MATE_TRANSCRIPTS":
        if (
            sv["sv_type"] != "BND"
            or not sv.get("mate_chrom")
            or sv.get("mate_pos") is None
        ):
            return {
                "source": "Ensembl", "action": action, "status": "not_applicable",
                "error": "a parsed BND mate is required", "retrieved_at": _now(),
            }
        mate_chrom = _clean_chrom(sv["mate_chrom"])
        mate_pos = _parse_integer(sv["mate_pos"], "mate_pos")
        mate_window = _breakpoint_window(
            mate_pos, sv.get("mate_confidence_interval"),
            CHROMOSOME_LENGTHS[build][mate_chrom],
        )
        scopes.append(("mate_breakend", mate_chrom, mate_window["interval"]))
    elif sv["end"] - sv["start"] + 1 <= 5_000_000:
        scopes.append(("nominal", chrom, [sv["start"], sv["end"]]))
    else:
        start_window = _breakpoint_window(
            sv["start"], sv.get("start_confidence_interval"), chrom_length
        )
        end_window = _breakpoint_window(
            sv["end"], sv.get("end_confidence_interval"), chrom_length
        )
        scopes.extend([
            ("start_breakend", chrom, start_window["interval"]),
            ("end_breakend", chrom, end_window["interval"]),
        ])
    results = [
        _query_ensembl_single_feature(host, scope_chrom, interval, feature, role)
        for role, scope_chrom, interval in scopes
    ]
    status = "found" if any(item["status"] == "found" for item in results) else (
        "error" if results and all(item["status"] == "error" for item in results)
        else "not_found"
    )
    return {
        "source": "Ensembl", "action": action, "status": status,
        "results": results, "retrieved_at": _now(),
        "limitations": (
            "Coordinate overlap with a transcript or exon is not a predicted "
            "molecular consequence."
        ),
    }


def _ncbi_params(extra: dict[str, Any]) -> dict[str, Any]:
    params = {**extra, "retmode": "json", "tool": "sv_investigator"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL
    return params


def _ncbi_json_request(
    endpoint: str, params: dict[str, Any]
) -> tuple[Any | None, str | None]:
    global _NCBI_LAST_REQUEST_MONOTONIC
    minimum_interval = 0.11 if NCBI_API_KEY else 0.34
    with _NCBI_REQUEST_LOCK:
        elapsed = time.monotonic() - _NCBI_LAST_REQUEST_MONOTONIC
        if elapsed < minimum_interval:
            time.sleep(minimum_interval - elapsed)
        _NCBI_LAST_REQUEST_MONOTONIC = time.monotonic()
        return _json_request(endpoint, params)


GNOMAD_SV_REGION_QUERY = """
query RegionStructuralVariants(
  $chrom: String!, $start: Int!, $stop: Int!,
  $referenceGenome: ReferenceGenomeId!,
  $dataset: StructuralVariantDatasetId!
) {
  region(
    chrom: $chrom, start: $start, stop: $stop,
    reference_genome: $referenceGenome
  ) {
    structural_variants(dataset: $dataset) {
      variant_id chrom chrom2 pos end pos2 end2 length type consequence
      ac an af ac_hom ac_hemi filters
    }
  }
}
"""


def _gnomad_type_compatible(query_type: str, database_type: Any) -> bool:
    observed = str(database_type or "").upper()
    compatible = {
        "DEL": {"DEL"},
        "DUP": {"DUP"},
        "INV": {"INV"},
        "INS": {"INS", "MEI"},
        "BND": {"BND", "CTX"},
        "CNV": {"CNV", "MCNV"},
    }
    return observed in compatible[query_type]


def _reciprocal_overlap(
    start_a: int, end_a: int, start_b: int, end_b: int
) -> tuple[float, float]:
    overlap = max(0, min(end_a, end_b) - max(start_a, start_b) + 1)
    length_a = end_a - start_a + 1
    length_b = end_b - start_b + 1
    return overlap / length_a, overlap / length_b


_MATCH_RANK = {
    "exact": 5,
    "high_similarity": 4,
    "partial_overlap": 3,
    "region_overlap": 2,
    "nearby": 1,
}


def _interval_candidate_match(
    sv: dict[str, Any],
    db_start: int,
    db_end: int,
    start_window: dict[str, Any],
    end_window: dict[str, Any],
) -> dict[str, Any]:
    """Classify an interval without treating heuristic padding as measured CI."""
    start, end = sv["start"], sv["end"]
    exact = db_start == start and db_end == end
    start_in_window = (
        start_window["is_measured_confidence_interval"]
        and start_window["interval"][0] <= db_start <= start_window["interval"][1]
    ) or db_start == start
    end_in_window = (
        end_window["is_measured_confidence_interval"]
        and end_window["interval"][0] <= db_end <= end_window["interval"][1]
    ) or db_end == end
    overlap_query, overlap_database = _reciprocal_overlap(
        start, end, db_start, db_end
    )
    query_length = max(1, end - start + 1)
    database_length = max(1, db_end - db_start + 1)
    size_similarity = min(query_length, database_length) / max(
        query_length, database_length
    )
    if exact:
        match_type = "exact"
    elif start_in_window and end_in_window and size_similarity >= 0.70:
        match_type = "high_similarity"
    elif min(overlap_query, overlap_database) >= 0.50:
        match_type = "partial_overlap"
    elif overlap_query > 0 and overlap_database > 0:
        match_type = "region_overlap"
    else:
        match_type = "nearby"
    return {
        "match_type": match_type,
        "coordinate_exact": exact,
        "same_event_established": False,
        "match_metrics": {
            "start_distance_bp": abs(db_start - start),
            "end_distance_bp": abs(db_end - end),
            "start_within_allowed_window": start_in_window,
            "end_within_allowed_window": end_in_window,
            "start_window_source": start_window["source"],
            "end_window_source": end_window["source"],
            "reciprocal_overlap_query": round(overlap_query, 6),
            "reciprocal_overlap_database": round(overlap_database, 6),
            "size_similarity": round(size_similarity, 6),
        },
    }


def _interval_query_context(
    sv: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], str]:
    """Return fixed match windows and bounded regions for external retrieval."""
    chrom_length = CHROMOSOME_LENGTHS[sv["genome_build"]][sv["chrom"]]
    start_window = _breakpoint_window(
        sv["start"], sv.get("start_confidence_interval"), chrom_length
    )
    end_window = _breakpoint_window(
        sv["end"], sv.get("end_confidence_interval"), chrom_length
    )
    expanded = [start_window["interval"][0], end_window["interval"][1]]
    if expanded[1] - expanded[0] + 1 <= 5_000_000:
        regions = [{"role": "nominal", "interval": expanded}]
        strategy = "expanded_full_interval"
    else:
        regions = [
            {"role": "start_breakpoint", "interval": start_window["interval"]},
            {"role": "end_breakpoint", "interval": end_window["interval"]},
        ]
        if regions[0]["interval"] == regions[1]["interval"]:
            regions = regions[:1]
        strategy = "separate_breakpoint_windows_for_large_sv"
    return start_window, end_window, regions, strategy


def _clingen_score(label: str) -> int | None:
    normalized = label.casefold()
    labels = (
        ("sufficient evidence", 3),
        ("emerging evidence", 2),
        ("little evidence", 1),
        ("no evidence", 0),
        ("autosomal recessive", 30),
        ("dosage sensitivity unlikely", 40),
    )
    for phrase, score in labels:
        if phrase in normalized:
            return score
    return None


def query_clingen_dosage(
    normalized_sv_json: str, max_records: int = MAX_DATABASE_RECORDS
) -> dict[str, Any]:
    """Query current ClinGen gene/region dosage curations by interval."""
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
        max_records = min(max(1, _parse_integer(max_records, "max_records")), 50)
    except (ValueError, TypeError) as exc:
        return {"source": "ClinGen Dosage", "status": "error", "error": str(exc)}
    if sv["sv_type"] not in {"DEL", "DUP", "CNV"}:
        return {
            "source": "ClinGen Dosage", "status": "not_applicable",
            "candidate_sv_type": sv["sv_type"], "records": [],
            "retrieved_at": _now(),
            "limitations": "Dosage sensitivity is queried only for DEL, DUP, and CNV.",
        }

    text, error = _text_request(CLINGEN_DOSAGE_CSV)
    if error or text is None:
        return {
            "source": "ClinGen Dosage", "status": "error",
            "error": error or "empty_response", "records": [],
            "source_url": CLINGEN_DOSAGE_CSV, "retrieved_at": _now(),
        }
    rows = list(csv.reader(io.StringIO(text)))
    created_at = ""
    header_index = None
    for index, row in enumerate(rows):
        first = row[0].strip() if row else ""
        if first.startswith("FILE CREATED:"):
            created_at = first.partition(":")[2].strip()
        if first == "GENE/REGION":
            header_index = index
            break
    if header_index is None:
        return {
            "source": "ClinGen Dosage", "status": "error",
            "error": "unrecognized_csv_header", "records": [],
            "source_url": CLINGEN_DOSAGE_CSV, "retrieved_at": _now(),
        }

    build_column = sv["genome_build"]
    start_window, end_window, _, _ = _interval_query_context(sv)
    parsed: list[dict[str, Any]] = []
    for values in rows[header_index + 1:]:
        if len(values) < len(rows[header_index]):
            continue
        row = dict(zip(rows[header_index], values))
        coordinate = row.get(build_column, "")
        match = re.fullmatch(r"chr([^:]+):(\d+)-(\d+)", coordinate.strip())
        if not match:
            continue
        try:
            db_chrom = _clean_chrom(match.group(1))
            db_start, db_end = int(match.group(2)), int(match.group(3))
        except ValueError:
            continue
        if db_chrom != sv["chrom"] or db_end < sv["start"] or db_start > sv["end"]:
            continue
        hi = row.get("HAPLOINSUFFICIENCY", "")
        ts = row.get("TRIPLOSENSITIVITY", "")
        direction = "haploinsufficiency" if sv["sv_type"] == "DEL" else (
            "triplosensitivity" if sv["sv_type"] == "DUP" else "both"
        )
        relevant = hi if direction == "haploinsufficiency" else (
            ts if direction == "triplosensitivity" else None
        )
        interval_match = _interval_candidate_match(
            sv, db_start, db_end, start_window, end_window,
        )
        identifier = row.get("HGNC/ISCA", "")
        parsed.append({
            "record_id": identifier,
            "entity": row.get("GENE/REGION", ""),
            "entity_type": "region" if identifier.startswith("ISCA-") else "gene",
            "chrom": db_chrom, "start": db_start, "end": db_end,
            "haploinsufficiency": {
                "assessment": hi, "score": _clingen_score(hi),
            },
            "triplosensitivity": {
                "assessment": ts, "score": _clingen_score(ts),
            },
            "relevant_dosage_direction": direction,
            "relevant_assessment": relevant,
            "curation_date": row.get("DATE", ""),
            "source_url": row.get("ONLINE REPORT", ""),
            **interval_match,
        })
    parsed.sort(key=lambda row: (
        row["entity_type"] != "region",
        -_MATCH_RANK[row["match_type"]],
        -row["match_metrics"]["reciprocal_overlap_query"],
        row["record_id"],
    ))
    records = parsed[:max_records]
    return {
        "source": "ClinGen Dosage", "status": "found" if records else "not_found",
        "completeness": "complete", "genome_build": sv["genome_build"],
        "candidate_sv_type": sv["sv_type"], "dataset_created_at": created_at,
        "records": records, "overlapping_record_count": len(parsed),
        "returned_record_count": len(records),
        "records_truncated": len(parsed) > max_records,
        "retrieved_at": _now(), "source_url": CLINGEN_DOSAGE_CSV,
        "limitations": (
            "ClinGen dosage scores are expert-curated gene/region evidence, not a "
            "patient-level classification. Coordinate overlap does not establish "
            "that recurrent breakpoints, copy state, phenotype, inheritance, or "
            "structural configuration match the curated cases."
        ),
    }


_CLINVAR_TYPE_TERMS = {
    "DEL": "Deletion[vartype]",
    "DUP": "Duplication[vartype]",
    "INV": "Inversion[vartype]",
    "INS": "Insertion[vartype]",
    "BND": "Translocation[vartype]",
    "CNV": "(Deletion[vartype] OR Duplication[vartype])",
}


def _clinvar_type_compatible(query_type: str, observed: Any) -> bool:
    value = str(observed or "").casefold()
    compatible = {
        "DEL": ("deletion", "copy number loss"),
        "DUP": ("duplication", "copy number gain"),
        "INV": ("inversion",),
        "INS": ("insertion",),
        "BND": ("translocation",),
        "CNV": ("deletion", "duplication", "copy number"),
    }
    return any(token in value for token in compatible[query_type])


def _clinvar_location(summary: dict[str, Any], build: str) -> dict[str, Any] | None:
    for variation in summary.get("variation_set") or []:
        for location in variation.get("variation_loc") or []:
            if location.get("assembly_name") != build:
                continue
            try:
                return {
                    "chrom": _clean_chrom(location.get("chr")),
                    "start": _parse_integer(location.get("start"), "ClinVar start"),
                    "end": _parse_integer(location.get("stop"), "ClinVar stop"),
                    "inner_start": location.get("inner_start") or None,
                    "inner_stop": location.get("inner_stop") or None,
                    "outer_start": location.get("outer_start") or None,
                    "outer_stop": location.get("outer_stop") or None,
                    "assembly_accession": location.get("assembly_acc_ver") or "",
                    "variant_type": variation.get("variant_type") or summary.get("obj_type"),
                }
            except (ValueError, TypeError):
                continue
    return None


def query_clinvar(
    normalized_sv_json: str, max_records: int = MAX_DATABASE_RECORDS
) -> dict[str, Any]:
    """Search ClinVar aggregate records and retain review status and conflicts."""
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
        max_records = min(max(1, _parse_integer(max_records, "max_records")), 50)
        start_window, end_window, regions, strategy = _interval_query_context(sv)
    except (ValueError, TypeError) as exc:
        return {"source": "ClinVar", "status": "error", "error": str(exc)}

    position_field = "chrpos38" if sv["genome_build"] == "GRCh38" else "chrpos37"
    query_errors: list[dict[str, Any]] = []
    ids: list[str] = []
    query_terms: list[str] = []
    search_limit = min(100, max(20, max_records * 5))
    for region in regions:
        interval = region["interval"]
        length_clause = "" if sv["sv_type"] == "BND" else " AND 50:100000000[varlen]"
        term = (
            f"{sv['chrom']}[chr] AND {interval[0]}:{interval[1]}[{position_field}] "
            f"AND {_CLINVAR_TYPE_TERMS[sv['sv_type']]}{length_clause}"
        )
        query_terms.append(term)
        payload, error = _ncbi_json_request(
            f"{NCBI_EUTILS}/esearch.fcgi",
            _ncbi_params({
                "db": "clinvar", "term": term, "retmax": search_limit,
            }),
        )
        result = payload.get("esearchresult") if isinstance(payload, dict) else None
        found_ids = result.get("idlist") if isinstance(result, dict) else None
        if error or not isinstance(found_ids, list):
            query_errors.append({**region, "error": error or "invalid_search_response_shape"})
            continue
        for uid in found_ids:
            if str(uid) not in ids:
                ids.append(str(uid))

    summaries: dict[str, Any] = {}
    if ids:
        payload, error = _ncbi_json_request(
            f"{NCBI_EUTILS}/esummary.fcgi",
            _ncbi_params({"db": "clinvar", "id": ",".join(ids)}),
        )
        result = payload.get("result") if isinstance(payload, dict) else None
        if error or not isinstance(result, dict):
            query_errors.append({
                "role": "summary", "error": error or "invalid_summary_response_shape"
            })
        else:
            summaries = result

    classified: list[dict[str, Any]] = []
    for uid in ids:
        summary = summaries.get(uid)
        if not isinstance(summary, dict):
            continue
        location = _clinvar_location(summary, sv["genome_build"])
        if not location or location["chrom"] != sv["chrom"]:
            continue
        if not _clinvar_type_compatible(sv["sv_type"], location["variant_type"]):
            continue
        interval_match = _interval_candidate_match(
            sv, location["start"], location["end"], start_window, end_window
        )
        classification = summary.get("germline_classification") or {}
        traits = [
            item.get("trait_name", "")
            for item in classification.get("trait_set") or []
            if isinstance(item, dict) and item.get("trait_name")
        ]
        submissions = summary.get("supporting_submissions") or {}
        accession = summary.get("accession_version") or summary.get("accession") or uid
        classified.append({
            "record_id": accession,
            "variation_id": uid,
            "title": summary.get("title", ""),
            "variant_type": location["variant_type"],
            "chrom": location["chrom"], "start": location["start"],
            "end": location["end"],
            "inner_start": location["inner_start"], "inner_stop": location["inner_stop"],
            "outer_start": location["outer_start"], "outer_stop": location["outer_stop"],
            "assembly_accession": location["assembly_accession"],
            "germline_classification": classification.get("description") or "not_provided",
            "review_status": classification.get("review_status") or "not_provided",
            "last_evaluated": classification.get("last_evaluated") or "",
            "traits": traits[:5], "trait_count": len(traits),
            "supporting_scv_count": len(submissions.get("scv") or []),
            "supporting_rcv_count": len(submissions.get("rcv") or []),
            "genes": [
                gene.get("symbol") for gene in summary.get("genes") or []
                if isinstance(gene, dict) and gene.get("symbol")
            ][:10],
            "source_url": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{uid}/",
            **interval_match,
        })
    classified.sort(key=lambda row: (
        -_MATCH_RANK[row["match_type"]],
        row["match_metrics"]["start_distance_bp"]
        + row["match_metrics"]["end_distance_bp"],
        row["record_id"],
    ))
    records = classified[:max_records]
    successful_queries = len(regions) - sum(
        error.get("role") != "summary" for error in query_errors
    )
    completeness = "complete" if not query_errors else (
        "failed" if successful_queries <= 0 else "partial"
    )
    status = "found" if records else (
        "not_found" if completeness == "complete" else "error"
    )
    return {
        "source": "ClinVar", "status": status, "completeness": completeness,
        "genome_build": sv["genome_build"], "candidate_sv_type": sv["sv_type"],
        "query_strategy": strategy, "query_regions": regions,
        "query_terms": query_terms, "breakpoint_windows": {
            "start": start_window, "end": end_window,
        },
        "records": records, "search_uid_count": len(ids),
        "compatible_record_count": len(classified),
        "returned_record_count": len(records),
        "records_truncated": len(classified) > max_records,
        "query_errors": query_errors, "retrieved_at": _now(),
        "source_url": "https://www.ncbi.nlm.nih.gov/clinvar/",
        "limitations": (
            "ClinVar contains submitted aggregate interpretations with different "
            "review levels and possible conflicts. Exact displayed coordinates and "
            "compatible type do not establish the same biological event. Inner/outer "
            "bounds, condition, review status, and last evaluation must be considered; "
            "absence from this bounded search does not establish novelty or benignity."
        ),
    }


_DBVAR_TYPE_TERMS = {
    "DEL": '(("deletion"[Variant Type]) OR ("copy number loss"[Variant Type]) '
           'OR ("copy number variation"[Variant Type]))',
    "DUP": '(("duplication"[Variant Type]) OR ("copy number gain"[Variant Type]) '
           'OR ("copy number variation"[Variant Type]))',
    "INV": '"inversion"[Variant Type]',
    "INS": '(("insertion"[Variant Type]) OR '
           '("mobile element insertion"[Variant Type]))',
    "CNV": '(("copy number variation"[Variant Type]) OR '
           '("copy number gain"[Variant Type]) OR '
           '("copy number loss"[Variant Type]) OR '
           '("deletion"[Variant Type]) OR ("duplication"[Variant Type]))',
}


def _bounded_list(value: Any, limit: int) -> list[Any]:
    if isinstance(value, list):
        return value[:limit]
    if value in (None, ""):
        return []
    return [value]


def _dbvar_type_compatibility(query_type: str, observed: Any) -> str | None:
    values = observed if isinstance(observed, list) else [observed]
    text = " ".join(str(value or "") for value in values).casefold()
    if query_type in {"DEL", "DUP"} and text.strip() == "copy number variation":
        return "ambiguous_cnv_direction"
    specific = {
        "DEL": ("deletion", "copy number loss"),
        "DUP": ("duplication", "copy number gain"),
        "INV": ("inversion",),
        "INS": ("insertion", "mobile element"),
        "CNV": (
            "copy number variation", "copy number gain", "copy number loss",
            "deletion", "duplication",
        ),
    }
    if any(token in text for token in specific[query_type]):
        return "compatible"
    return None


def _dbvar_build_placement(
    summary: dict[str, Any], build: str, chrom: str
) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for placement in summary.get("dbvarplacementlist") or []:
        if not isinstance(placement, dict):
            continue
        assembly = str(placement.get("assembly") or "")
        try:
            placement_chrom = _clean_chrom(placement.get("chr"))
            db_start = _parse_integer(placement.get("chr_start"), "dbVar start")
            db_end = _parse_integer(placement.get("chr_end"), "dbVar end")
        except (ValueError, TypeError):
            continue
        if assembly.startswith(build) and placement_chrom == chrom and db_start <= db_end:
            matches.append({
                "chrom": placement_chrom,
                "start": db_start,
                "end": db_end,
                "assembly": assembly,
                "assembly_accession": placement.get("assembly_accession") or "",
            })
    if not matches:
        return None
    matches.sort(key=lambda item: (item["assembly"] != build, item["start"], item["end"]))
    return matches[0]


def query_dbvar(
    normalized_sv_json: str, max_records: int = MAX_DATABASE_RECORDS
) -> dict[str, Any]:
    """Search build-matched dbVar variant regions through NCBI E-utilities."""
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
        max_records = min(max(1, _parse_integer(max_records, "max_records")), 50)
        start_window, end_window, regions, strategy = _interval_query_context(sv)
    except (ValueError, TypeError) as exc:
        return {"source": "NCBI dbVar", "status": "error", "error": str(exc)}
    if sv["sv_type"] == "BND":
        return {
            "source": "NCBI dbVar", "status": "not_applicable",
            "candidate_sv_type": "BND", "records": [],
            "reason": "E-utilities summaries do not expose a reliable mate adjacency.",
            "retrieved_at": _now(),
        }

    search_limit = min(100, max(20, max_records * 5))
    ids: list[str] = []
    query_terms: list[str] = []
    search_counts: list[dict[str, Any]] = []
    query_errors: list[dict[str, Any]] = []
    for region in regions:
        interval = region["interval"]
        term = (
            f'{sv["chrom"]}[Chr] AND '
            f'({interval[0]}:{interval[1]}[ChrPos] OR '
            f'{interval[0]}:{interval[1]}[ChrEnd]) AND '
            f'{_DBVAR_TYPE_TERMS[sv["sv_type"]]} AND "variant"[Object Type]'
        )
        query_terms.append(term)
        payload, error = _ncbi_json_request(
            f"{NCBI_EUTILS}/esearch.fcgi",
            _ncbi_params({
                "db": "dbvar", "term": term, "retmax": search_limit,
            }),
        )
        result = payload.get("esearchresult") if isinstance(payload, dict) else None
        found_ids = result.get("idlist") if isinstance(result, dict) else None
        if error or not isinstance(found_ids, list):
            query_errors.append({**region, "error": error or "invalid_search_response_shape"})
            continue
        try:
            total_count = _parse_integer(result.get("count", len(found_ids)), "dbVar count")
        except (ValueError, TypeError):
            total_count = len(found_ids)
        search_counts.append({
            **region, "total_count": total_count,
            "uid_count_returned": len(found_ids),
            "search_truncated": total_count > len(found_ids),
        })
        for uid in found_ids:
            if str(uid) not in ids:
                ids.append(str(uid))

    summaries: dict[str, Any] = {}
    if ids:
        payload, error = _ncbi_json_request(
            f"{NCBI_EUTILS}/esummary.fcgi",
            _ncbi_params({"db": "dbvar", "id": ",".join(ids)}),
        )
        result = payload.get("result") if isinstance(payload, dict) else None
        if error or not isinstance(result, dict):
            query_errors.append({
                "role": "summary", "error": error or "invalid_summary_response_shape"
            })
        else:
            summaries = result

    classified: list[dict[str, Any]] = []
    for uid in ids:
        summary = summaries.get(uid)
        if not isinstance(summary, dict):
            continue
        placement = _dbvar_build_placement(summary, sv["genome_build"], sv["chrom"])
        if placement is None:
            continue
        observed_types = summary.get("dbvarvarianttypelist") or []
        compatibility = _dbvar_type_compatibility(sv["sv_type"], observed_types)
        if compatibility is None:
            continue
        interval_match = _interval_candidate_match(
            sv, placement["start"], placement["end"], start_window, end_window
        )
        variant_id = summary.get("sv") or uid
        classified.append({
            "record_id": variant_id,
            "uid": uid,
            "study_id": summary.get("st") or "",
            "object_type": summary.get("obj_type") or "",
            "variant_types": observed_types,
            "type_compatibility": compatibility,
            **placement,
            "variant_call_count": summary.get("variant_call_count"),
            "clinical_significance": _bounded_list(
                summary.get("dbvarclinicalsignificancelist"), 5
            ),
            "genes": _bounded_list(summary.get("dbvargenelist"), 10),
            "methods": _bounded_list(summary.get("dbvarmethodlist"), 5),
            "publications": _bounded_list(summary.get("dbvarpublicationlist"), 5),
            "source_url": f"https://www.ncbi.nlm.nih.gov/dbvar/variants/{variant_id}/",
            **interval_match,
        })
    classified.sort(key=lambda row: (
        row["type_compatibility"] != "compatible",
        -_MATCH_RANK[row["match_type"]],
        row["match_metrics"]["start_distance_bp"]
        + row["match_metrics"]["end_distance_bp"],
        row["record_id"],
    ))
    records = classified[:max_records]
    search_failures = sum(error.get("role") != "summary" for error in query_errors)
    successful_queries = len(regions) - search_failures
    completeness = "complete" if not query_errors else (
        "failed" if successful_queries <= 0 else "partial"
    )
    status = "found" if records else (
        "not_found" if completeness == "complete" else "error"
    )
    return {
        "source": "NCBI dbVar", "status": status,
        "completeness": completeness, "genome_build": sv["genome_build"],
        "candidate_sv_type": sv["sv_type"], "query_strategy": strategy,
        "query_regions": regions, "query_terms": query_terms,
        "breakpoint_windows": {"start": start_window, "end": end_window},
        "search_counts": search_counts, "records": records,
        "search_uid_count": len(ids),
        "search_results_truncated": any(
            item["search_truncated"] for item in search_counts
        ),
        "compatible_record_count": len(classified),
        "returned_record_count": len(records),
        "records_truncated": len(classified) > max_records,
        "query_errors": query_errors, "retrieved_at": _now(),
        "source_url": "https://www.ncbi.nlm.nih.gov/dbvar/",
        "limitations": (
            "dbVar aggregates submitter-defined variant regions and calls from many "
            "studies and technologies. Boundaries may be imprecise or remapped, a "
            "generic copy-number type may not establish DEL versus DUP direction, "
            "and this bounded endpoint search does not retrieve every enclosing "
            "record. A match is contextual evidence, not proof of event identity, "
            "clinical significance, or validation."
        ),
    }


def _dgv_type_compatible(query_type: str, row: dict[str, Any]) -> bool:
    observed = f"{row.get('variant_type', '')} {row.get('variant_sub_type', '')}".casefold()
    compatible = {
        "DEL": ("loss", "deletion"),
        "DUP": ("gain", "duplication"),
        "INV": ("inversion",),
        "INS": ("insertion",),
        "CNV": ("cnv", "gain", "loss", "duplication", "deletion"),
    }
    return any(token in observed for token in compatible.get(query_type, ()))


def query_dgv(
    normalized_sv_json: str, max_records: int = MAX_DATABASE_RECORDS
) -> dict[str, Any]:
    """Query the DGV Gold Standard hg19/hg38 track through the UCSC API."""
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
        max_records = min(max(1, _parse_integer(max_records, "max_records")), 50)
        start_window, end_window, regions, strategy = _interval_query_context(sv)
    except (ValueError, TypeError) as exc:
        return {"source": "DGV Gold Standard", "status": "error", "error": str(exc)}
    if sv["sv_type"] == "BND":
        return {
            "source": "DGV Gold Standard", "status": "not_applicable",
            "candidate_sv_type": "BND", "records": [], "retrieved_at": _now(),
            "limitations": "The DGV Gold Standard CNV track is not used for BND matching.",
        }

    genome = "hg38" if sv["genome_build"] == "GRCh38" else "hg19"
    raw_records: dict[str, dict[str, Any]] = {}
    query_errors: list[dict[str, Any]] = []
    data_version = ""
    for region in regions:
        interval = region["interval"]
        payload, error = _json_request(
            f"{UCSC_API}/getData/track",
            {
                "genome": genome, "track": "dgvGold", "chrom": f"chr{sv['chrom']}",
                "start": interval[0] - 1, "end": interval[1],
            },
        )
        rows = payload.get("dgvGold") if isinstance(payload, dict) else None
        if error or not isinstance(rows, list):
            query_errors.append({**region, "error": error or "invalid_response_shape"})
            continue
        data_version = payload.get("dataTime") or data_version
        for row in rows:
            if isinstance(row, dict) and (row.get("dgvID") or row.get("name")):
                raw_records[str(row.get("dgvID") or row.get("name"))] = row

    classified: list[dict[str, Any]] = []
    for record_id, row in raw_records.items():
        if not _dgv_type_compatible(sv["sv_type"], row):
            continue
        try:
            db_start = _parse_integer(row.get("chromStart"), "DGV chromStart") + 1
            db_end = _parse_integer(row.get("chromEnd"), "DGV chromEnd")
        except (ValueError, TypeError):
            continue
        interval_match = _interval_candidate_match(
            sv, db_start, db_end, start_window, end_window
        )
        studies = [item.strip() for item in str(row.get("Studies") or "").split(",") if item.strip()]
        platforms = [item.strip() for item in str(row.get("Platforms") or "").split(",") if item.strip()]
        source_variants = [
            item.strip() for item in str(row.get("variants") or "").split(",")
            if item.strip()
        ]
        classified.append({
            "record_id": record_id,
            "variant_type": row.get("variant_type") or "",
            "variant_sub_type": row.get("variant_sub_type") or "",
            "chrom": sv["chrom"], "start": db_start, "end": db_end,
            "frequency": row.get("Frequency") or "not_provided",
            "num_unique_samples_tested": row.get("num_unique_samples_tested"),
            "num_samples_with_variant": row.get("num_samples"),
            "num_studies": row.get("num_studies"),
            "studies": studies[:5], "study_names_truncated": len(studies) > 5,
            "num_platforms": row.get("num_platforms"),
            "platforms": platforms[:5], "platform_names_truncated": len(platforms) > 5,
            "num_source_variants": row.get("num_variants"),
            "source_variant_ids": source_variants[:5],
            "source_variant_ids_truncated": len(source_variants) > 5,
            "source_url": (
                f"https://api.genome.ucsc.edu/getData/track?genome={genome};"
                f"track=dgvGold;chrom=chr{sv['chrom']};start={db_start - 1};end={db_end}"
            ),
            **interval_match,
        })
    classified.sort(key=lambda row: (
        -_MATCH_RANK[row["match_type"]],
        row["match_metrics"]["start_distance_bp"]
        + row["match_metrics"]["end_distance_bp"],
        row["record_id"],
    ))
    records = classified[:max_records]
    successful_queries = len(regions) - len(query_errors)
    completeness = "complete" if not query_errors else (
        "failed" if successful_queries == 0 else "partial"
    )
    status = "found" if records else (
        "not_found" if completeness == "complete" else "error"
    )
    return {
        "source": "DGV Gold Standard", "status": status,
        "completeness": completeness, "genome_build": sv["genome_build"],
        "candidate_sv_type": sv["sv_type"], "dataset": "dgvGold",
        "access_backend": "UCSC Genome Browser API", "data_version": data_version,
        "query_strategy": strategy, "query_regions": regions,
        "breakpoint_windows": {"start": start_window, "end": end_window},
        "records": records, "raw_region_record_count": len(raw_records),
        "compatible_record_count": len(classified),
        "returned_record_count": len(records),
        "records_truncated": len(classified) > max_records,
        "query_errors": query_errors, "retrieved_at": _now(),
        "source_url": "https://dgv.tcag.ca/dgv/app/downloads",
        "limitations": (
            "This adapter queries the curated DGV Gold Standard track exposed by "
            "UCSC, not the complete current DGV release. DGV aggregates healthy-control "
            "studies with heterogeneous platforms and often imprecise boundaries. "
            "Overlap or frequency is contextual population evidence, not proof of the "
            "same event, benignity, or absence of clinical effect."
        ),
    }


def _classify_gnomad_candidate(
    sv: dict[str, Any],
    row: dict[str, Any],
    start_window: dict[str, Any],
    end_window: dict[str, Any],
    mate_window: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    query_type = sv["sv_type"]
    if not _gnomad_type_compatible(query_type, row.get("type")):
        return None
    try:
        db_start = _parse_integer(row.get("pos"), "gnomAD pos")
        db_end_value = row.get("end")
        if db_end_value is None and query_type in {"INS", "BND"}:
            db_end_value = db_start
        db_end = _parse_integer(db_end_value, "gnomAD end")
    except ValueError:
        return None

    start = sv["start"]
    end = sv["end"]
    start_distance = abs(db_start - start)
    end_distance = abs(db_end - end)
    # A heuristic fallback widens retrieval, but is not a measured confidence
    # interval and must not by itself upgrade a candidate's similarity class.
    start_in_window = (
        start_window["is_measured_confidence_interval"]
        and start_window["interval"][0] <= db_start <= start_window["interval"][1]
    ) or db_start == start
    end_in_window = (
        end_window["is_measured_confidence_interval"]
        and end_window["interval"][0] <= db_end <= end_window["interval"][1]
    ) or db_end == end
    exact = db_start == start and db_end == end

    metrics: dict[str, Any] = {
        "start_distance_bp": start_distance,
        "end_distance_bp": end_distance,
        "start_within_allowed_window": start_in_window,
        "end_within_allowed_window": end_in_window,
        "start_window_source": start_window["source"],
        "end_window_source": end_window["source"],
    }
    if query_type == "BND" and sv.get("mate_chrom") and sv.get("mate_pos"):
        db_chrom2_value = row.get("chrom2")
        db_pos2_value = row.get("pos2")
        if db_pos2_value is None:
            db_pos2_value = row.get("end2")
        if db_pos2_value is None and str(db_chrom2_value) != str(row.get("chrom")):
            db_pos2_value = row.get("end")
        if db_chrom2_value is None or db_pos2_value is None or mate_window is None:
            return None
        try:
            db_chrom1 = _clean_chrom(row.get("chrom"))
            db_chrom2 = _clean_chrom(db_chrom2_value)
            db_pos2 = _parse_integer(db_pos2_value, "gnomAD pos2")
        except (ValueError, TypeError):
            return None

        input_chrom1 = sv["chrom"]
        input_chrom2 = sv["mate_chrom"]
        direct = db_chrom1 == input_chrom1 and db_chrom2 == input_chrom2
        swapped = db_chrom1 == input_chrom2 and db_chrom2 == input_chrom1
        if not direct and not swapped:
            return None
        if direct:
            db_local_pos, db_mate_pos = db_start, db_pos2
            database_order = "same_as_input"
        else:
            db_local_pos, db_mate_pos = db_pos2, db_start
            database_order = "swapped_relative_to_input"
        local_distance = abs(db_local_pos - start)
        mate_distance = abs(db_mate_pos - sv["mate_pos"])
        local_in_window = (
            start_window["is_measured_confidence_interval"]
            and start_window["interval"][0] <= db_local_pos <= start_window["interval"][1]
        ) or db_local_pos == start
        mate_in_window = (
            mate_window["is_measured_confidence_interval"]
            and mate_window["interval"][0] <= db_mate_pos <= mate_window["interval"][1]
        ) or db_mate_pos == sv["mate_pos"]
        exact = local_distance == 0 and mate_distance == 0
        if exact:
            match_type = "exact"
        elif local_in_window and mate_in_window:
            match_type = "high_similarity"
        elif local_in_window or mate_in_window:
            match_type = "partial_overlap"
        else:
            match_type = "nearby"
        metrics = {
            "comparison_scope": "both_breakends",
            "database_breakend_order": database_order,
            "chromosome_pair_matches": True,
            "local_breakpoint_distance_bp": local_distance,
            "mate_breakpoint_distance_bp": mate_distance,
            "local_breakpoint_within_allowed_window": local_in_window,
            "mate_breakpoint_within_allowed_window": mate_in_window,
            "local_window_source": start_window["source"],
            "mate_window_source": mate_window["source"],
            "orientation_comparison": "not_available_in_gnomad_response",
        }
    elif query_type in {"INS", "BND"}:
        if exact:
            match_type = "exact"
        elif start_in_window:
            match_type = "high_similarity"
        else:
            match_type = "nearby"
        metrics["comparison_scope"] = (
            "insertion_point" if query_type == "INS" else "first_breakend_only"
        )
        if query_type == "BND":
            metrics["mate_status"] = "not_provided"
            # An exact first coordinate cannot establish identity for a BND.
            if match_type == "exact":
                match_type = "high_similarity"
            exact = False
    else:
        overlap_query, overlap_database = _reciprocal_overlap(
            start, end, db_start, db_end
        )
        query_length = max(1, end - start + 1)
        database_length = max(1, db_end - db_start + 1)
        size_similarity = min(query_length, database_length) / max(
            query_length, database_length
        )
        metrics.update({
            "reciprocal_overlap_query": round(overlap_query, 6),
            "reciprocal_overlap_database": round(overlap_database, 6),
            "size_similarity": round(size_similarity, 6),
        })
        if exact:
            match_type = "exact"
        elif start_in_window and end_in_window and size_similarity >= 0.70:
            match_type = "high_similarity"
        elif min(overlap_query, overlap_database) >= 0.50:
            match_type = "partial_overlap"
        elif overlap_query > 0 and overlap_database > 0:
            match_type = "region_overlap"
        else:
            match_type = "nearby"

    rank = {
        "exact": 5,
        "high_similarity": 4,
        "partial_overlap": 3,
        "region_overlap": 2,
        "nearby": 1,
    }
    return {
        **row,
        "match_type": match_type,
        "match_metrics": metrics,
        "same_event_established": exact,
        "interpretation": (
            "Exact coordinate and compatible-type match."
            if exact else
            "Candidate similarity only; the available evidence does not establish "
            "that this is the same biological event."
        ),
        "source_url": (
            f"https://gnomad.broadinstitute.org/variant/{row.get('variant_id')}"
            f"?dataset={sv['gnomad_dataset']}"
        ),
        "_rank": rank[match_type],
    }


def query_gnomad_sv(
    normalized_sv_json: str,
    max_records: int = MAX_DATABASE_RECORDS,
    retrieval_padding_bp: int = 0,
) -> dict[str, Any]:
    """Query build-matched gnomAD-SV and classify similar candidate records.

    The tool uses VCF confidence intervals when present. Missing sides use a
    configurable heuristic window for retrieval only; the window is never presented
    as a measured confidence interval or proof that two records are the same event.
    """
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
        genome_build = sv["genome_build"]
        chrom = sv["chrom"]
        start = sv["start"]
        end = sv["end"]
        sv_type = sv["sv_type"]
        chromosome_length = CHROMOSOME_LENGTHS[genome_build][chrom]
        start_window = _breakpoint_window(
            start, sv.get("start_confidence_interval"), chromosome_length
        )
        end_window = _breakpoint_window(
            end, sv.get("end_confidence_interval"), chromosome_length
        )
        mate_chrom = sv.get("mate_chrom") if sv_type == "BND" else None
        mate_pos = sv.get("mate_pos") if sv_type == "BND" else None
        mate_window: dict[str, Any] | None = None
        if mate_chrom is not None and mate_pos is not None:
            mate_chrom = _clean_chrom(mate_chrom)
            mate_pos = _parse_integer(mate_pos, "mate_pos")
            mate_chromosome_length = CHROMOSOME_LENGTHS[genome_build][mate_chrom]
            if not 1 <= mate_pos <= mate_chromosome_length:
                raise ValueError("mate_pos is outside the mate chromosome")
            mate_window = _breakpoint_window(
                mate_pos, sv.get("mate_confidence_interval"), mate_chromosome_length
            )
        max_records = min(max(1, _parse_integer(max_records, "max_records")), 50)
        retrieval_padding_bp = _parse_integer(
            retrieval_padding_bp, "retrieval_padding_bp"
        )
        if retrieval_padding_bp not in {0, 2_000, 10_000}:
            raise ValueError("retrieval_padding_bp must be 0, 2000, or 10000")
    except (ValueError, TypeError) as exc:
        return {"source": "gnomAD-SV", "status": "error", "error": str(exc)}

    dataset = "gnomad_sv_r4" if genome_build == "GRCh38" else "gnomad_sv_r2_1"
    sv = {
        **sv, "chrom": chrom, "start": start, "end": end, "sv_type": sv_type,
        "mate_chrom": mate_chrom, "mate_pos": mate_pos, "gnomad_dataset": dataset,
    }
    if sv_type == "BND" and mate_window is not None:
        query_regions = [
            {
                "role": "local_breakend", "chrom": chrom,
                "interval": start_window["interval"],
            },
            {
                "role": "mate_breakend", "chrom": mate_chrom,
                "interval": mate_window["interval"],
            },
        ]
        query_strategy = "paired_breakend_windows"
    else:
        expanded_interval = [start_window["interval"][0], end_window["interval"][1]]
        if expanded_interval[1] - expanded_interval[0] + 1 <= 5_000_000:
            query_regions = [
                {"role": "nominal", "chrom": chrom, "interval": expanded_interval}
            ]
            query_strategy = "expanded_full_interval"
        else:
            query_regions = [
                {
                    "role": "start_breakpoint", "chrom": chrom,
                    "interval": start_window["interval"],
                },
                {
                    "role": "end_breakpoint", "chrom": chrom,
                    "interval": end_window["interval"],
                },
            ]
            query_strategy = "separate_breakpoint_windows_for_large_sv"
            if query_regions[0]["interval"] == query_regions[1]["interval"]:
                query_regions = query_regions[:1]

    # Widen only the API retrieval region.  Candidate classification below still
    # uses start_window/end_window/mate_window exactly as it did at baseline.
    matching_query_regions = [
        {**region, "interval": list(region["interval"])} for region in query_regions
    ]
    if retrieval_padding_bp:
        query_regions = [
            {
                **region,
                "interval": [
                    max(1, region["interval"][0] - retrieval_padding_bp),
                    min(
                        CHROMOSOME_LENGTHS[genome_build][region["chrom"]],
                        region["interval"][1] + retrieval_padding_bp,
                    ),
                ],
            }
            for region in query_regions
        ]

    raw_records: dict[str, dict[str, Any]] = {}
    query_errors: list[dict[str, Any]] = []
    for query_region in query_regions:
        interval = query_region["interval"]
        payload, error = _json_post(GNOMAD_GRAPHQL, {
            "query": GNOMAD_SV_REGION_QUERY,
            "variables": {
                "chrom": query_region["chrom"],
                "start": interval[0],
                "stop": interval[1],
                "referenceGenome": genome_build,
                "dataset": dataset,
            },
        })
        if error:
            query_errors.append({**query_region, "error": error})
            continue
        if not isinstance(payload, dict) or payload.get("errors"):
            query_errors.append({
                **query_region,
                "error": "graphql_error",
                "details": payload.get("errors") if isinstance(payload, dict) else None,
            })
            continue
        rows = payload.get("data", {}).get("region", {}).get("structural_variants")
        if not isinstance(rows, list):
            query_errors.append({**query_region, "error": "invalid_response_shape"})
            continue
        for row in rows:
            if isinstance(row, dict) and row.get("variant_id"):
                raw_records[str(row["variant_id"])] = row

    classified = []
    rejected_type_count = 0
    rejected_bnd_topology_count = 0
    for row in raw_records.values():
        if not _gnomad_type_compatible(sv_type, row.get("type")):
            rejected_type_count += 1
            continue
        match = _classify_gnomad_candidate(
            sv, row, start_window, end_window, mate_window
        )
        if match is None:
            if sv_type == "BND" and mate_window is not None:
                rejected_bnd_topology_count += 1
        else:
            classified.append(match)
    classified.sort(
        key=lambda row: (
            -row["_rank"],
            row["match_metrics"].get("start_distance_bp", 0)
            + row["match_metrics"].get("end_distance_bp", 0)
            + row["match_metrics"].get("local_breakpoint_distance_bp", 0)
            + row["match_metrics"].get("mate_breakpoint_distance_bp", 0),
            str(row.get("variant_id")),
        )
    )
    records = []
    for row in classified[:max_records]:
        records.append({key: value for key, value in row.items() if key != "_rank"})

    successful_queries = len(query_regions) - len(query_errors)
    completeness = "complete" if not query_errors else (
        "failed" if successful_queries == 0 else "partial"
    )
    status = "found" if records else (
        "not_found" if completeness == "complete" else "error"
    )
    return {
        "source": "gnomAD-SV",
        "status": status,
        "completeness": completeness,
        "genome_build": genome_build,
        "dataset": dataset,
        "candidate_sv_type": sv_type,
        "query_strategy": query_strategy,
        "query_intervals": [region["interval"] for region in query_regions],
        "query_regions": query_regions,
        "matching_query_regions": matching_query_regions,
        "retrieval_padding_bp": retrieval_padding_bp,
        "matching_windows_unchanged": True,
        "breakpoint_windows": {
            "start": start_window, "end": end_window, "mate": mate_window,
        },
        "records": records,
        "raw_region_record_count": len(raw_records),
        "compatible_record_count": len(classified),
        "returned_record_count": len(records),
        "type_incompatible_records_excluded": rejected_type_count,
        "bnd_topology_or_coordinate_records_excluded": rejected_bnd_topology_count,
        "records_truncated": len(classified) > max_records,
        "query_errors": query_errors,
        "retrieved_at": _now(),
        "source_url": "https://gnomad.broadinstitute.org/",
        "limitations": (
            "Similarity classes are deterministic screening labels, not proof of "
            "variant identity or biological effect. Heuristic windows are used only "
            "when VCF breakpoint confidence intervals are unavailable. BND records "
            "with a parsed mate are compared using both breakends and the chromosome "
            "pair, allowing reversed record order. Input orientation is retained but "
            "cannot be compared because it is absent from this gnomAD response. BND "
            "records without a mate retain first-breakend-only candidate matching. "
            "Adaptive retrieval padding, when nonzero, widens only the records "
            "retrieved from the API; it never widens the fixed matching windows. "
            "A gnomAD-SV absence "
            "does not establish novelty, pathogenicity, or technical validity."
        ),
    }


def search_pubmed(query: str, max_records: int = MAX_PUBMED_RECORDS) -> dict[str, Any]:
    """Search PubMed and return citation metadata.

    Args:
        query: A traceable PubMed query using coordinates, genes, or SV terms.
        max_records: Maximum citation summaries to return.

    Returns:
        PubMed IDs and summaries. A title alone is not treated as claim support.
    """
    query = query.strip()
    if not query:
        return {"source": "PubMed", "status": "error", "error": "empty_query"}
    max_records = max(1, min(int(max_records), MAX_PUBMED_RECORDS))
    search, error = _ncbi_json_request(
        f"{NCBI_EUTILS}/esearch.fcgi",
        _ncbi_params({"db": "pubmed", "term": query, "retmax": max_records, "sort": "relevance"}),
    )
    if error:
        return {"source": "PubMed", "status": "error", "error": error, "query": query}
    search_result = search.get("esearchresult") if isinstance(search, dict) else None
    ids = search_result.get("idlist") if isinstance(search_result, dict) else None
    if not isinstance(ids, list):
        return {
            "source": "PubMed", "status": "error",
            "error": "invalid_search_response_shape", "query": query,
        }
    ids = ids[:max_records]
    if not ids:
        return {
            "source": "PubMed", "status": "not_found", "query": query,
            "records": [], "retrieved_at": _now(),
        }
    summaries, summary_error = _ncbi_json_request(
        f"{NCBI_EUTILS}/esummary.fcgi",
        _ncbi_params({"db": "pubmed", "id": ",".join(ids)}),
    )
    if summary_error:
        return {"source": "PubMed", "status": "error", "error": summary_error, "query": query}
    result = summaries.get("result") if isinstance(summaries, dict) else None
    if not isinstance(result, dict):
        return {
            "source": "PubMed", "status": "error",
            "error": "invalid_summary_response_shape", "query": query,
        }
    records = []
    for pmid in ids:
        row = result.get(pmid, {})
        if isinstance(row, dict):
            raw_authors = row.get("authors") or []
            if not isinstance(raw_authors, list):
                raw_authors = []
            author_names = [
                author.get("name") if isinstance(author, dict) else str(author)
                for author in raw_authors
            ]
            author_names = [name for name in author_names if name]
            article_ids = row.get("articleids") or []
            records.append({
                "pmid": pmid,
                "title": row.get("title"),
                "authors": author_names[:3],
                "author_count": len(author_names),
                "authors_truncated": len(author_names) > 3,
                "source": row.get("source"),
                "pubdate": row.get("pubdate"),
                "doi": next((
                    item.get("value") for item in article_ids
                    if isinstance(item, dict) and item.get("idtype") == "doi"
                ), None),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
    if not records:
        return {
            "source": "PubMed", "status": "error",
            "error": "summary_records_missing", "query": query,
            "retrieved_at": _now(),
        }
    return {
        "source": "PubMed", "status": "found", "query": query,
        "records": records, "retrieved_at": _now(),
        "summary_records_missing": len(ids) - len(records),
        "limitations": "Metadata does not prove that the full text supports a biological claim.",
    }


def assess_artifact_risk(
    normalized_sv_json: str, region_annotation_json: str = "{}"
) -> dict[str, Any]:
    """Apply deterministic first-pass artifact-risk rules.

    Args:
        normalized_sv_json: JSON returned by normalize_sv_input.
        region_annotation_json: JSON produced by the region annotation agent.

    Returns:
        Risk items with present/absent/unknown status. Unknown is never converted
        to absence.
    """
    try:
        sv = _safe_json_loads(normalized_sv_json, "normalized_sv_json")
        annotation = _safe_json_loads(region_annotation_json, "region_annotation_json")
    except ValueError as exc:
        return {"overall_risk": "unknown", "error": str(exc), "risk_items": []}
    quality = sv.get("quality") or {}
    items: list[dict[str, Any]] = []

    def add(
        name: str,
        status: str,
        impact: str,
        check: str,
        evidence: Any = None,
    ) -> None:
        items.append({
            "risk_type": name, "status": status, "impact": impact,
            "recommended_check": check, "evidence": evidence,
        })

    call_rate = quality.get("call_rate")
    if call_rate is None:
        add(
            "low_call_rate",
            "unknown",
            "Missingness can produce spurious population differences.",
            "Calculate call rate per cohort.",
        )
    else:
        try:
            if isinstance(call_rate, bool):
                raise ValueError
            rate = float(call_rate)
            if not 0 <= rate <= 1:
                raise ValueError
            add(
                "low_call_rate",
                "present" if rate < 0.95 else "absent",
                f"Reported call rate is {rate:.3f}.",
                "Inspect cohort-specific missingness and genotype clusters.",
                rate,
            )
        except (TypeError, ValueError):
            add(
                "low_call_rate",
                "unknown",
                "The supplied call rate is not a valid fraction.",
                "Provide a numeric rate between 0 and 1.",
                call_rate,
            )

    caller = quality.get("caller")
    caller_count = len(caller) if isinstance(caller, list) else (1 if caller else 0)
    add(
        "single_caller_support",
        "unknown"
        if caller_count == 0
        else ("present" if caller_count == 1 else "absent"),
        "A call from one algorithm may reflect caller-specific bias.",
        "Validate with an orthogonal caller or experimental assay.",
        caller,
    )

    def find_repeat_list(value: Any) -> list[Any] | None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in {"repeat", "repeats"} and isinstance(child, list):
                    return child
                found = find_repeat_list(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_repeat_list(child)
                if found is not None:
                    return found
        return None

    breakpoint_annotations = annotation.get("breakpoint_annotations")
    repeat_rows: list[Any] | None
    repeat_evidence: Any
    if isinstance(breakpoint_annotations, dict):
        breakpoint_repeat_lists = []
        for name in ("start", "end"):
            item = breakpoint_annotations.get(name, {})
            features = item.get("features", {}) if isinstance(item, dict) else {}
            breakpoint_repeat_lists.append(
                features.get("repeat") if isinstance(features, dict) else None
            )
        observed_repeats = [
            row
            for rows in breakpoint_repeat_lists
            if isinstance(rows, list)
            for row in rows
        ]
        if observed_repeats:
            repeat_rows = observed_repeats
        elif all(isinstance(rows, list) for rows in breakpoint_repeat_lists):
            repeat_rows = []
        else:
            repeat_rows = None
        repeat_evidence = {
            "scope": "breakpoint_windows",
            "start_repeat_count": (
                len(breakpoint_repeat_lists[0])
                if isinstance(breakpoint_repeat_lists[0], list) else None
            ),
            "end_repeat_count": (
                len(breakpoint_repeat_lists[1])
                if isinstance(breakpoint_repeat_lists[1], list) else None
            ),
        }
    else:
        repeat_rows = find_repeat_list(annotation)
        repeat_evidence = (
            len(repeat_rows) if repeat_rows is not None else None
        )
    add(
        "repeat_region",
        "unknown" if repeat_rows is None else ("present" if repeat_rows else "absent"),
        "Repeats in breakpoint windows can make breakpoint placement unreliable.",
        "Confirm both breakpoints against a curated repeat track.",
        repeat_evidence,
    )
    add(
        "low_mappability",
        "unknown",
        "Low-mappability sequence can create ambiguous alignments.",
        "Intersect both breakpoints with a build-matched mappability track.",
    )

    supporting_reads = quality.get("supporting_reads")
    has_numeric_support = isinstance(supporting_reads, (int, float)) and not isinstance(
        supporting_reads, bool
    )
    add(
        "supporting_reads",
        "present" if has_numeric_support and supporting_reads <= 0 else "unknown",
        "Weak read support increases false-positive risk.",
        "Review caller-specific split-read, paired-end, and depth thresholds.",
        supporting_reads,
    )

    genotype_quality = quality.get("genotype_quality")
    if isinstance(genotype_quality, (int, float)) and not isinstance(
        genotype_quality, bool
    ):
        gq_status = "present" if genotype_quality < 20 else "absent"
    else:
        gq_status = "unknown"
    add(
        "genotype_quality",
        gq_status,
        "Low or missing genotype quality weakens frequency estimates.",
        "Inspect genotype likelihoods and quality distributions by cohort.",
        genotype_quality,
    )

    batch_checked = quality.get("batch_checked")
    add(
        "batch_effect",
        "absent" if batch_checked is True else ("present" if batch_checked is False else "unknown"),
        "Unequal pipelines or batches can mimic population differentiation.",
        "Compare sequencing, coverage, and calling batches between cohorts.",
        batch_checked,
    )

    statuses = [item["status"] for item in items]
    overall = "high" if statuses.count("present") >= 2 else (
        "medium" if "present" in statuses else "unknown" if "unknown" in statuses else "low"
    )
    return {"overall_risk": overall, "risk_items": items}


def _add_ensembl_evidence_ids(annotation: dict[str, Any]) -> dict[str, Any]:
    """Add stable local IDs without deleting or summarizing source fields."""
    # Keep caller-owned raw evidence untouched while preserving native JSON values.
    enriched = copy.deepcopy(annotation)

    def enrich_feature_map(container: dict[str, Any], role: str) -> None:
        features = container.get("features")
        if not isinstance(features, dict):
            return
        for feature, rows in features.items():
            if not isinstance(rows, list):
                continue
            for index, row in enumerate(rows, start=1):
                if isinstance(row, dict):
                    row.setdefault(
                        "evidence_id",
                        f"ENS-BL-{role.upper()}-{feature.upper()}-{index:03d}",
                    )
                    row.setdefault("feature_type", feature)
                    row.setdefault("breakpoint_role", role)

    enrich_feature_map(enriched, "nominal")
    breakpoints = enriched.get("breakpoint_annotations")
    if isinstance(breakpoints, dict):
        for role in ("start", "end", "mate"):
            item = breakpoints.get(role)
            if isinstance(item, dict):
                enrich_feature_map(item, role)
    return enriched


def _add_gnomad_evidence_ids(evidence: dict[str, Any], prefix: str) -> dict[str, Any]:
    enriched = copy.deepcopy(evidence)
    for index, row in enumerate(enriched.get("records") or [], start=1):
        if isinstance(row, dict):
            row.setdefault("evidence_id", f"GNO-{prefix}-{index:03d}")
    return enriched


def _add_database_evidence_ids(
    evidence: dict[str, Any], source_prefix: str
) -> dict[str, Any]:
    """Attach local evidence IDs while keeping the adapter response intact."""
    enriched = copy.deepcopy(evidence)
    for index, row in enumerate(enriched.get("records") or [], start=1):
        if isinstance(row, dict):
            row.setdefault("evidence_id", f"{source_prefix}-BL-{index:03d}")
    return enriched


def collect_baseline_evidence(normalized_sv_json: str) -> dict[str, Any]:
    """Collect all non-optional annotation, population, clinical, and QC evidence."""
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
    except (ValueError, TypeError) as exc:
        return {"status": "blocked", "error": str(exc)}

    # Independent public sources run concurrently. The artifact assessment waits for
    # Ensembl because repeat overlap is one of its deterministic risk inputs.
    with ThreadPoolExecutor(max_workers=7) as executor:
        region_future = executor.submit(
            query_ensembl_region,
            genome_build=sv["genome_build"], chrom=sv["chrom"],
            start=sv["start"], end=sv["end"], sv_type=sv["sv_type"],
            start_confidence_interval=sv.get("start_confidence_interval"),
            end_confidence_interval=sv.get("end_confidence_interval"),
            mate_chrom=sv.get("mate_chrom"), mate_pos=sv.get("mate_pos"),
            mate_confidence_interval=sv.get("mate_confidence_interval"),
        )
        gnomad_future = executor.submit(query_gnomad_sv, normalized_sv_json)
        vep_future = executor.submit(query_ensembl_vep, normalized_sv_json)
        clingen_future = executor.submit(query_clingen_dosage, normalized_sv_json)
        clinvar_future = executor.submit(query_clinvar, normalized_sv_json)
        dbvar_future = executor.submit(query_dbvar, normalized_sv_json)
        dgv_future = executor.submit(query_dgv, normalized_sv_json)
        region = region_future.result()
        population = gnomad_future.result()
        vep = vep_future.result()
        clingen = clingen_future.result()
        clinvar = clinvar_future.result()
        dbvar = dbvar_future.result()
        dgv = dgv_future.result()
    artifact = assess_artifact_risk(normalized_sv_json, json.dumps(region))
    return {
        "status": "complete",
        "collection_policy": "deterministic_non_optional_baseline",
        "immutable_candidate_fields": {
            key: sv.get(key) for key in (
                "genome_build", "chrom", "start", "end", "sv_type",
                "start_confidence_interval", "end_confidence_interval",
                "mate_chrom", "mate_pos", "mate_confidence_interval",
            )
        },
        "region_annotation": _add_ensembl_evidence_ids(region),
        "database_evidence": _add_gnomad_evidence_ids(population, "BL"),
        "vep_evidence": _add_database_evidence_ids(vep, "VEP"),
        "clingen_dosage_evidence": _add_database_evidence_ids(clingen, "CGD"),
        "clinvar_evidence": _add_database_evidence_ids(clinvar, "CLV"),
        "dbvar_evidence": _add_database_evidence_ids(dbvar, "DBV"),
        "dgv_evidence": _add_database_evidence_ids(dgv, "DGV"),
        "artifact_risk": artifact,
        "retrieved_at": _now(),
        "limitations": [
            "Baseline Ensembl evidence is coordinate-overlap evidence.",
            "Ensembl VEP consequences are predictions for a symbolic SV allele, not "
            "experimental validation or a patient-level interpretation.",
            "Population evidence includes gnomAD-SV and the DGV Gold Standard track; "
            "the latter is not the complete current DGV release.",
            "dbVar evidence aggregates heterogeneous submitted studies and may include "
            "imprecise, remapped, or direction-ambiguous records.",
            "Clinical evidence includes ClinGen dosage curations and ClinVar aggregate "
            "records, neither of which is a patient-level diagnosis.",
            "Missing source data and query failures remain explicit unknown/error states.",
        ],
    }


def execute_adaptive_action(
    normalized_sv_json: str, action: str
) -> dict[str, Any]:
    """Execute exactly one whitelisted follow-up without changing candidate identity."""
    if action not in ADAPTIVE_ACTIONS:
        return {
            "status": "rejected", "action": action,
            "error": "action_not_whitelisted",
            "allowed_actions": sorted(ADAPTIVE_ACTIONS),
        }
    try:
        sv = _validated_normalized_sv(normalized_sv_json)
    except (ValueError, TypeError) as exc:
        return {"status": "rejected", "action": action, "error": str(exc)}

    if action.startswith("EXPAND_GNOMAD_RETRIEVAL_"):
        padding = 2_000 if action.endswith("2KB") else 10_000
        result = query_gnomad_sv(
            normalized_sv_json, retrieval_padding_bp=padding
        )
        result = _add_gnomad_evidence_ids(result, f"ADP-{padding}")
    else:
        result = _ensembl_adaptive_query(sv, action)
    return {
        "status": "executed", "action": action,
        "candidate_fields_unchanged": True,
        "result": result,
    }


def run_budgeted_adaptive_action(
    normalized_sv_json: str,
    action: str,
    evidence_gap: str,
    reason: str,
    expected_information_gain: str,
    state: MutableMapping[str, Any],
) -> dict[str, Any]:
    """Atomically reserve adaptive budget and append a machine-readable audit."""
    history_key = "temp:adaptive_action_history"
    count_key = "temp:adaptive_query_count"
    audit = {
        "action": action,
        "evidence_gap": evidence_gap.strip(),
        "reason": reason.strip(),
        "expected_information_gain": expected_information_gain.strip(),
        "attempted_at": _now(),
    }
    with _ADAPTIVE_STATE_LOCK:
        history = list(state.get(history_key, []))
        used = int(state.get(count_key, 0))
        if not all((
            audit["evidence_gap"],
            audit["reason"],
            audit["expected_information_gain"],
        )):
            rejection_reason = "missing_action_justification"
        elif action not in ADAPTIVE_ACTIONS:
            rejection_reason = "action_not_whitelisted"
        elif any(
            item.get("action") == action
            and item.get("status") in {"executing", "executed"}
            for item in history
        ):
            rejection_reason = "duplicate_action"
        elif used >= MAX_ADAPTIVE_QUERIES:
            rejection_reason = "query_budget_exhausted"
        else:
            rejection_reason = None

        if rejection_reason is not None:
            audit.update({
                "status": "rejected",
                "rejection_reason": rejection_reason,
            })
            history.append(audit)
            state[history_key] = history
            return {
                **audit,
                "queries_used": used,
                "queries_remaining": max(0, MAX_ADAPTIVE_QUERIES - used),
            }

        # Reserve before releasing the lock. A failed external request still consumes
        # budget, and another concurrent call now sees the updated count and action.
        used += 1
        audit["status"] = "executing"
        audit_index = len(history)
        history.append(audit)
        state[count_key] = used
        state[history_key] = history

    result = execute_adaptive_action(normalized_sv_json, action)
    nested_result = result.get("result")
    result_status = (
        nested_result.get("status")
        if isinstance(nested_result, dict) else result.get("status")
    )
    audit.update({"status": "executed", "result_status": result_status})
    with _ADAPTIVE_STATE_LOCK:
        history = list(state.get(history_key, []))
        history[audit_index] = audit
        state[history_key] = history
    return {
        **audit, "queries_used": used,
        "queries_remaining": MAX_ADAPTIVE_QUERIES - used,
        "result": result,
    }
