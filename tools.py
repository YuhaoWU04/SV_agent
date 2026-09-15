"""Deterministic validation and public database adapters.

All functions return JSON-compatible dictionaries. A database failure is data:
it is represented by an explicit status and does not masquerade as no evidence.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .config import (
    HTTP_TIMEOUT_SECONDS,
    MAX_DATABASE_RECORDS,
    MAX_PUBMED_RECORDS,
    NCBI_API_KEY,
    NCBI_EMAIL,
    OMIM_API_KEY,
    USER_AGENT,
)


ENSEMBL_REST = "https://rest.ensembl.org"
NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SUPPORTED_BUILDS = {"GRCh37", "GRCh38"}
SUPPORTED_TYPES = {"DEL", "DUP", "INV", "INS", "BND", "CNV"}
COORDINATE_SYSTEM = "1-based-inclusive"

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
) -> tuple[Any | None, str | None]:
    query = f"?{urlencode(params, doseq=True)}" if params else ""
    request_headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = Request(f"{url}{query}", headers=request_headers)
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
        if interval_length <= 0:
            raise ValueError("SV interval length must be positive")

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
            "sv_type": sv_type,
            "sv_type_original": original_sv_type,
            "sv_subtype": sv_subtype,
            "length_bp": length_bp,
            "statistics": statistics,
            "quality": quality,
            "source_record": payload.get("source_record"),
            "warnings": warnings,
            "normalizations": normalizations,
        }
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return {"status": "validation_error", "error": str(exc), "raw_input": raw_input}


def query_ensembl_region(
    genome_build: str,
    chrom: str,
    start: int,
    end: int,
) -> dict[str, Any]:
    """Query genes, regulatory features, and repeats overlapping an SV interval.

    Args:
        genome_build: GRCh37 or GRCh38.
        chrom: Chromosome without a required chr prefix.
        start: One-based inclusive start coordinate.
        end: One-based inclusive end coordinate.

    Returns:
        Evidence records grouped by Ensembl feature type.
    """
    if genome_build not in SUPPORTED_BUILDS:
        return {"source": "Ensembl", "status": "error", "error": "unsupported_build"}
    try:
        chrom = _clean_chrom(chrom)
        start, end = int(start), int(end)
    except (ValueError, TypeError) as exc:
        return {"source": "Ensembl", "status": "error", "error": str(exc)}
    host = "https://grch37.rest.ensembl.org" if genome_build == "GRCh37" else ENSEMBL_REST
    region = quote(f"{chrom}:{start}-{end}", safe=":-")
    collected: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for feature in ("gene", "regulatory", "repeat"):
        payload, error = _json_request(
            f"{host}/overlap/region/human/{region}",
            {"feature": feature},
            {"Content-Type": "application/json"},
        )
        if error:
            errors[feature] = error
            collected[feature] = []
        else:
            rows = payload if isinstance(payload, list) else []
            collected[feature] = rows[:MAX_DATABASE_RECORDS]
    status = "error" if errors and len(errors) == 3 else (
        "found" if any(collected.values()) else "not_found"
    )
    return {
        "source": "Ensembl",
        "status": status,
        "genome_build": genome_build,
        "query_region": f"{chrom}:{start}-{end}",
        "match_type": "region_overlap",
        "features": collected,
        "errors": errors,
        "retrieved_at": _now(),
        "source_url": f"{host}/overlap/region/human/{region}",
        "limitations": "Results are capped per feature type; transcript consequence prediction is not included.",
    }


def _ncbi_params(extra: dict[str, Any]) -> dict[str, Any]:
    params = {**extra, "retmode": "json", "tool": "sv_investigator"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL
    return params


def query_clinvar_region(
    genome_build: str,
    chrom: str,
    start: int,
    end: int,
    max_records: int = MAX_DATABASE_RECORDS,
) -> dict[str, Any]:
    """Find ClinVar records indexed in the candidate interval.

    Args:
        genome_build: GRCh37 or GRCh38 assembly label.
        chrom: Chromosome without a required chr prefix.
        start: One-based inclusive start coordinate.
        end: One-based inclusive end coordinate.
        max_records: Maximum summaries to return.

    Returns:
        Region-level ClinVar matches. They are not asserted to be exact SV matches.
    """
    if genome_build not in SUPPORTED_BUILDS:
        return {"source": "ClinVar", "status": "error", "error": "unsupported_build"}
    try:
        chrom = _clean_chrom(chrom)
        start, end = int(start), int(end)
    except (ValueError, TypeError) as exc:
        return {"source": "ClinVar", "status": "error", "error": str(exc)}
    position_field = "chrpos37" if genome_build == "GRCh37" else "chrpos38"
    term = f"{chrom}[chr] AND {start}:{end}[{position_field}]"
    search, error = _json_request(
        f"{NCBI_EUTILS}/esearch.fcgi",
        _ncbi_params({"db": "clinvar", "term": term, "retmax": min(max_records, 20)}),
    )
    if error:
        return {"source": "ClinVar", "status": "error", "error": error, "query": term}
    ids = search.get("esearchresult", {}).get("idlist", []) if isinstance(search, dict) else []
    if not ids:
        return {
            "source": "ClinVar", "status": "not_found", "query": term,
            "match_type": "region_search", "records": [], "retrieved_at": _now(),
            "limitations": "No indexed region match is not evidence of benignity.",
        }
    summaries, summary_error = _json_request(
        f"{NCBI_EUTILS}/esummary.fcgi",
        _ncbi_params({"db": "clinvar", "id": ",".join(ids)}),
    )
    if summary_error:
        return {"source": "ClinVar", "status": "error", "error": summary_error, "query": term}
    result = summaries.get("result", {}) if isinstance(summaries, dict) else {}
    records = [result[item_id] for item_id in ids if isinstance(result.get(item_id), dict)]
    return {
        "source": "ClinVar", "status": "found", "query": term,
        "genome_build": genome_build, "match_type": "region_search",
        "records": records, "retrieved_at": _now(),
        "source_url": "https://www.ncbi.nlm.nih.gov/clinvar/",
        "limitations": "Region hits require a separate coordinate/type review before being called exact matches.",
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
    search, error = _json_request(
        f"{NCBI_EUTILS}/esearch.fcgi",
        _ncbi_params({"db": "pubmed", "term": query, "retmax": min(max_records, 20), "sort": "relevance"}),
    )
    if error:
        return {"source": "PubMed", "status": "error", "error": error, "query": query}
    ids = search.get("esearchresult", {}).get("idlist", []) if isinstance(search, dict) else []
    if not ids:
        return {
            "source": "PubMed", "status": "not_found", "query": query,
            "records": [], "retrieved_at": _now(),
        }
    summaries, summary_error = _json_request(
        f"{NCBI_EUTILS}/esummary.fcgi",
        _ncbi_params({"db": "pubmed", "id": ",".join(ids)}),
    )
    if summary_error:
        return {"source": "PubMed", "status": "error", "error": summary_error, "query": query}
    result = summaries.get("result", {}) if isinstance(summaries, dict) else {}
    records = []
    for pmid in ids:
        row = result.get(pmid, {})
        if isinstance(row, dict):
            records.append({
                "pmid": pmid,
                "title": row.get("title"),
                "authors": row.get("authors", []),
                "source": row.get("source"),
                "pubdate": row.get("pubdate"),
                "doi": next((x.get("value") for x in row.get("articleids", []) if x.get("idtype") == "doi"), None),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
    return {
        "source": "PubMed", "status": "found", "query": query,
        "records": records, "retrieved_at": _now(),
        "limitations": "Metadata does not prove that the full text supports a biological claim.",
    }


def database_availability() -> dict[str, Any]:
    """Report which planned database adapters exist in the MVP.

    Returns:
        Configuration status for all databases named in the research plan.
    """
    return {
        "Ensembl": {"status": "configured", "adapter": "query_ensembl_region"},
        "ClinVar": {"status": "configured", "adapter": "query_clinvar_region"},
        "PubMed": {"status": "configured", "adapter": "search_pubmed"},
        "OMIM": {"status": "not_queried" if OMIM_API_KEY else "unavailable", "reason": "licensed API; adapter pending"},
        "gnomAD-SV": {"status": "not_queried", "reason": "adapter pending"},
        "dbVar": {"status": "not_queried", "reason": "adapter pending"},
        "DGV": {"status": "not_queried", "reason": "adapter pending"},
        "GWAS Catalog": {"status": "not_queried", "reason": "adapter pending"},
        "GO": {"status": "not_queried", "reason": "adapter pending"},
        "Reactome": {"status": "not_queried", "reason": "adapter pending"},
    }


def assess_artifact_risk(normalized_sv_json: str, region_annotation_json: str = "{}") -> dict[str, Any]:
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

    def add(name: str, status: str, impact: str, check: str, evidence: Any = None) -> None:
        items.append({
            "risk_type": name, "status": status, "impact": impact,
            "recommended_check": check, "evidence": evidence,
        })

    call_rate = quality.get("call_rate")
    if call_rate is None:
        add("low_call_rate", "unknown", "Missingness can produce spurious population differences.", "Calculate call rate per cohort.")
    else:
        try:
            rate = float(call_rate)
            add("low_call_rate", "present" if rate < 0.95 else "absent", f"Reported call rate is {rate:.3f}.", "Inspect cohort-specific missingness and genotype clusters.", rate)
        except (TypeError, ValueError):
            add("low_call_rate", "unknown", "The supplied call rate is not numeric.", "Provide a numeric rate between 0 and 1.", call_rate)

    caller = quality.get("caller")
    caller_count = len(caller) if isinstance(caller, list) else (1 if caller else 0)
    add(
        "single_caller_support",
        "unknown" if caller_count == 0 else ("present" if caller_count == 1 else "absent"),
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

    repeat_rows = find_repeat_list(annotation)
    add(
        "repeat_region",
        "unknown" if repeat_rows is None else ("present" if repeat_rows else "absent"),
        "Repeats can make breakpoints unreliable.",
        "Confirm both breakpoints against a curated repeat track.",
        len(repeat_rows) if repeat_rows is not None else None,
    )
    add(
        "low_mappability",
        "unknown",
        "Low-mappability sequence can create ambiguous alignments.",
        "Intersect both breakpoints with a build-matched mappability track.",
    )

    supporting_reads = quality.get("supporting_reads")
    add(
        "supporting_reads",
        "present" if isinstance(supporting_reads, (int, float)) and supporting_reads <= 0 else "unknown",
        "Weak read support increases false-positive risk.",
        "Review caller-specific split-read, paired-end, and depth thresholds.",
        supporting_reads,
    )

    genotype_quality = quality.get("genotype_quality")
    if isinstance(genotype_quality, (int, float)):
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
