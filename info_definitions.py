"""Deterministic INFO descriptions; unknown fields are never expanded by guessing."""

import copy
from typing import Any


VCF_STANDARD_INFO = {
    "AC": "Allele count in genotypes, for each ALT allele, in the same order as listed.",
    "AF": "Allele frequency for each ALT allele, in the same order as listed.",
    "AN": "Total number of alleles in called genotypes.",
    "NS": "Number of samples with data.",
    "DP": "Combined depth across samples.",
    "END": "End position of the variant described in this record.",
    "SVTYPE": "Type of structural variant.",
    "SVLEN": "Difference in length between REF and ALT alleles.",
    "CIPOS": "Confidence interval around POS for imprecise variants.",
    "CIEND": "Confidence interval around END for imprecise variants.",
    "IMPRECISE": "Imprecise structural variation.",
}

# These descriptions match the mergedSV.v8 GRCh38 INFO header, not all SV datasets.
INFO_1000G_SV = {
    "TSD": "Precise Target Site Duplication for bases, if unknown, value will be NULL",
    "SVTYPE": "Type of structural variant",
    "MSTART": "Mitochondrial start coordinate of inserted sequence",
    "MLEN": "Estimated length of mitochondrial insert",
    "MEND": "Mitochondrial end coordinate of inserted sequence",
    "MEINFO": "Mobile element info of the form NAME,START,END<POLARITY; If there is only 5' OR 3' support for this call, will be NULL NULL for START and END",
    "SVLEN": "Difference in length between REF and ALT alleles",
    "IMPRECISE": "Imprecise structural variation",
    "CIEND": "Confidence interval around END for imprecise variants",
    "CIPOS": "Confidence interval around POS for imprecise variants",
    "END": "End coordinate of this variant",
    "CS": "Source call set.",
    "MC": "Merged calls.",
    "AF": "Estimated allele frequency in the range (0,1)",
    "NS": "Number of samples with data",
    "SITEPOST": "Site Median posterior probability from MVNcall.",
    "AC": "Allele count in genotypes",
    "AN": "Total number of alleles in called genotypes",
    **{f"{group}_AF": f"Allele frequency in the {group} populations calculated from AC and AN, in the range (0,1)"
       for group in ("EAS", "EUR", "AFR", "AMR", "SAS")},
}


def resolve_info_definitions(
    info: dict[str, Any], provided: Any = None, dataset: Any = None,
) -> dict[str, dict[str, str]]:
    """Resolve present INFO fields, recording provided versus fallback descriptions."""
    if provided is None:
        provided = {}
    if not isinstance(provided, dict):
        raise ValueError("source_record.info_definition must be a JSON object")
    dataset_definitions = INFO_1000G_SV if str(dataset).strip().upper() == "1000G-SV" else {}
    definitions = {}
    for field in info:
        if field in provided:
            value = provided[field]
            description = value.get("description") if isinstance(value, dict) else value
            if not isinstance(description, str) or not description.strip():
                raise ValueError(f"source_record.info_definition.{field} must contain a non-empty description")
            # Caller-supplied origin labels are not independently verified.
            source = "provided"
        elif field in dataset_definitions:
            description, source = dataset_definitions[field], "1000g_dictionary"
        elif field in VCF_STANDARD_INFO:
            description, source = VCF_STANDARD_INFO[field], "vcf_standard"
        else:
            continue
        definitions[field] = {"description": description, "source": source}
    return definitions


def query_info_descriptions(normalized_sv: Any, field_ids: list[str]) -> dict[str, Any]:
    """Read requested INFO values beside saved definitions without modifying state."""
    if not isinstance(field_ids, list) or not field_ids or any(
        not isinstance(field, str) or not field.strip() for field in field_ids
    ):
        return {"status": "rejected", "error": "field_ids_must_be_a_non_empty_list_of_INFO_names"}
    record = normalized_sv.get("source_record") if isinstance(normalized_sv, dict) else None
    info = record.get("INFO", record.get("info")) if isinstance(record, dict) else None
    if not isinstance(info, dict):
        return {"status": "unavailable", "error": "current_SV_has_no_INFO_record"}
    definitions = record.get("info_definition") or {}
    fields, missing, undefined = {}, [], []
    for field in dict.fromkeys(field_ids):
        if field not in info:
            missing.append(field)
            continue
        definition = definitions.get(field, {}) if isinstance(definitions, dict) else {}
        description = definition.get("description") if isinstance(definition, dict) else None
        if not isinstance(description, str) or not description.strip():
            description = None
            undefined.append(field)
        fields[field] = {
            "value": copy.deepcopy(info[field]),
            "description": description,
            "source": definition.get("source") if description else None,
        }
    return {"status": "complete", "fields": fields,
            "missing_fields": missing, "undefined_fields": undefined}
