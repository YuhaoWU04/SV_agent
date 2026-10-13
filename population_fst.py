"""Screen biallelic population SVs with the SG10K-SV Fst workflow."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import allel


SV_TYPE_ALIASES = {
    "DEL": "DEL", "CN0": "DEL",
    "DUP": "DUP", "CNV": "CNV", "INV": "INV", "INS": "INS",
    "ALU": "INS", "LINE": "INS", "LINE1": "INS", "SVA": "INS",
    "MEI": "INS",
}

CANDIDATE_SORT_ORDER = "maximum Fst descending, BH q-value ascending, then SV ID ascending"


@dataclass(frozen=True)
class Variant:
    chrom: str
    pos: int
    variant_id: str
    ref: str
    alt: str
    filter: str
    info: dict[str, str | bool]
    sv_type: str
    end: int
    length_bp: int | None


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open(encoding="utf-8")


def parse_region(value: str) -> tuple[str, int, int] | None:
    if value.lower() in {"all", "genome", "autosomes"}:
        return None
    match = re.fullmatch(r"(?:chr)?([^:]+):(\d+)-(\d+)", value.replace(",", ""), re.I)
    if not match:
        raise ValueError("region must be 'all' or look like chr2:1000000-3000000")
    chrom, start, end = match.group(1), int(match.group(2)), int(match.group(3))
    if start < 1 or end < start:
        raise ValueError("region must satisfy 1 <= start <= end")
    return chrom, start, end


def load_panel(path: Path, populations: Iterable[str]) -> dict[str, str]:
    wanted = list(dict.fromkeys(populations))
    if len(wanted) < 2:
        raise ValueError("at least two distinct populations are required")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        if not rows.fieldnames or not {"sample", "pop"}.issubset(rows.fieldnames):
            raise ValueError("panel must contain tab-separated sample and pop columns")
        selected = {
            str(row["sample"]): str(row["pop"])
            for row in rows
            if row.get("sample") and row.get("pop") in wanted
        }
    counts = {population: sum(value == population for value in selected.values()) for population in wanted}
    missing = [population for population, count in counts.items() if count < 2]
    if missing:
        raise ValueError("populations with fewer than two panel samples: " + ", ".join(missing))
    return selected


def _parse_info(text: str) -> dict[str, str | bool]:
    result: dict[str, str | bool] = {}
    for item in text.split(";"):
        key, separator, value = item.partition("=")
        result[key] = value if separator else True
    return result


def _parse_int(value: object) -> int | None:
    try:
        return int(str(value).split(",", 1)[0])
    except (TypeError, ValueError):
        return None


def _normalize_sv_type(info: dict[str, str | bool], alt: str) -> str | None:
    raw = str(info.get("SVTYPE") or alt.strip("<>")).upper()
    raw = raw.split(":", 1)[0]
    return SV_TYPE_ALIASES.get(raw)


def _parse_gt(sample_field: str, gt_index: int) -> tuple[int, int] | None:
    fields = sample_field.split(":")
    if gt_index >= len(fields):
        return None
    alleles = re.split(r"[|/]", fields[gt_index])
    if len(alleles) != 2:
        return None
    try:
        parsed = tuple(-1 if allele == "." else int(allele) for allele in alleles)
    except ValueError:
        return None
    if any(allele not in {-1, 0, 1} for allele in parsed):
        return None
    return parsed  # type: ignore[return-value]


def read_vcf_region(
    path: Path,
    sample_population: dict[str, str],
    region: tuple[str, int, int] | None,
) -> tuple[list[Variant], np.ndarray, np.ndarray, dict[str, int]]:
    autosomes = {str(chrom) for chrom in range(1, 23)}
    selected_columns: list[int] = []
    labels: list[str] = []
    variants: list[Variant] = []
    genotype_rows: list[np.ndarray] = []
    skipped = {"outside_region": 0, "multiallelic": 0, "unsupported_type": 0, "invalid_gt": 0}

    with _open_text(path) as handle:
        for line in handle:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                header = line.rstrip("\n").split("\t")
                for index, sample in enumerate(header[9:], start=9):
                    if sample in sample_population:
                        selected_columns.append(index)
                        labels.append(sample_population[sample])
                if not selected_columns:
                    raise ValueError("no requested panel samples occur in the VCF")
                continue
            if line.startswith("#"):
                continue
            if not selected_columns:
                raise ValueError("VCF #CHROM header was not found")

            fields = line.rstrip("\n").split("\t")
            record_chrom = fields[0].removeprefix("chr")
            position = int(fields[1])
            in_region = (
                record_chrom in autosomes if region is None
                else record_chrom == region[0] and region[1] <= position <= region[2]
            )
            if not in_region:
                skipped["outside_region"] += 1
                continue
            if "," in fields[4]:
                skipped["multiallelic"] += 1
                continue
            info = _parse_info(fields[7])
            sv_type = _normalize_sv_type(info, fields[4])
            if sv_type is None:
                skipped["unsupported_type"] += 1
                continue
            if len(fields) <= selected_columns[-1]:
                skipped["invalid_gt"] += 1
                continue
            formats = fields[8].split(":")
            if "GT" not in formats:
                skipped["invalid_gt"] += 1
                continue
            gt_index = formats.index("GT")
            genotypes = np.full((len(selected_columns), 2), -1, dtype=np.int8)
            valid = True
            for output_index, column in enumerate(selected_columns):
                parsed = _parse_gt(fields[column], gt_index)
                if parsed is None:
                    valid = False
                    break
                genotypes[output_index] = parsed
            if not valid:
                skipped["invalid_gt"] += 1
                continue

            record_end = _parse_int(info.get("END"))
            if record_end is None:
                record_end = position if sv_type == "INS" else position + max(0, len(fields[3]) - 1)
            length = _parse_int(info.get("SVLEN"))
            variants.append(Variant(
                chrom=record_chrom,
                pos=position,
                variant_id=fields[2] if fields[2] != "." else f"{record_chrom}:{position}:{sv_type}",
                ref=fields[3],
                alt=fields[4],
                filter=fields[6],
                info=info,
                sv_type=sv_type,
                end=max(position, record_end),
                length_bp=abs(length) if length not in (None, 0) else None,
            ))
            genotype_rows.append(genotypes)

    if not variants:
        raise ValueError("no supported biallelic SVs were found in the requested region")
    label_array = np.asarray(labels, dtype=str)
    populations = list(dict.fromkeys(sample_population.values()))
    missing = [population for population in populations if np.count_nonzero(label_array == population) < 2]
    if missing:
        raise ValueError("requested populations missing from VCF: " + ", ".join(missing))
    return variants, np.stack(genotype_rows), label_array, skipped


def _allele_counts(genotypes: np.ndarray, labels: np.ndarray, population: str) -> tuple[np.ndarray, np.ndarray]:
    selected = genotypes[:, labels == population, :]
    return np.count_nonzero(selected == 1, axis=(1, 2)), np.count_nonzero(selected >= 0, axis=(1, 2))


def hudson_fst(alt1: np.ndarray, an1: np.ndarray, alt2: np.ndarray, an2: np.ndarray) -> np.ndarray:
    """Hudson Fst for biallelic sites using scikit-allel."""
    shape = alt1.shape
    ac1 = np.stack((an1 - alt1, alt1), axis=-1).reshape(-1, 2)
    ac2 = np.stack((an2 - alt2, alt2), axis=-1).reshape(-1, 2)
    numerator, denominator = allel.hudson_fst(ac1, ac2)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (numerator / denominator).reshape(shape)


def _pairwise_fst(genotypes: np.ndarray, labels: np.ndarray, populations: list[str]) -> tuple[list[str], np.ndarray]:
    counts = {population: _allele_counts(genotypes, labels, population) for population in populations}
    names: list[str] = []
    values: list[np.ndarray] = []
    for first, second in combinations(populations, 2):
        names.append(f"{first}_vs_{second}")
        values.append(hudson_fst(*counts[first], *counts[second]))
    raw = np.stack(values, axis=1)
    # The SG10K-SV figure code replaces negative/missing values with zero before max.
    return names, np.where(np.isfinite(raw) & (raw > 0), raw, 0.0)


def bh_fdr(p_values: np.ndarray) -> np.ndarray:
    count = len(p_values)
    order = np.argsort(p_values, kind="stable")
    ranked = p_values[order] * count / np.arange(1, count + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted = np.empty(count, dtype=float)
    adjusted[order] = np.minimum(ranked, 1.0)
    return adjusted


def calculate(
    genotypes: np.ndarray,
    labels: np.ndarray,
    populations: list[str],
    *,
    permutations: int,
    seed: int,
) -> dict[str, Any]:
    if permutations < 1:
        raise ValueError("permutations must be positive")
    pair_names, observed_pairs = _pairwise_fst(genotypes, labels, populations)
    observed_max = observed_pairs.max(axis=1)
    max_index = observed_pairs.argmax(axis=1)
    exceedances = np.zeros(len(genotypes), dtype=np.int64)
    rng = np.random.default_rng(seed)
    memberships = {
        population: np.empty((len(labels), permutations), dtype=np.float32)
        for population in populations
    }
    for iteration in range(permutations):
        shuffled = rng.permutation(labels)
        for population in populations:
            memberships[population][:, iteration] = shuffled == population

    # ponytail: fixed 1,000-SV blocks bound memory; expose a knob only if profiling needs one.
    for start in range(0, len(genotypes), 1000):
        stop = min(start + 1000, len(genotypes))
        block = genotypes[start:stop]
        called = block >= 0
        dosage = np.where(called, block, 0).sum(axis=2).astype(np.float32)
        allele_number = called.sum(axis=2).astype(np.float32)
        counts = {
            population: (
                dosage @ memberships[population],
                allele_number @ memberships[population],
            )
            for population in populations
        }
        permuted_max = np.zeros((stop - start, permutations), dtype=float)
        for first, second in combinations(populations, 2):
            values = hudson_fst(*counts[first], *counts[second])
            values = np.where(np.isfinite(values) & (values > 0), values, 0.0)
            np.maximum(permuted_max, values, out=permuted_max)
        exceedances[start:stop] = np.count_nonzero(
            permuted_max >= observed_max[start:stop, None], axis=1
        )
    # Match the authors' released Figure 4 code: right tail, floor zero at 1/B.
    p_values = exceedances / permutations
    p_values[p_values == 0] = 1 / permutations
    return {
        "pair_names": pair_names,
        "pair_fst": observed_pairs,
        "fst_max": observed_max,
        "fst_max_pair": np.asarray(pair_names, dtype=object)[max_index],
        "p_value": p_values,
        "q_value": bh_fdr(p_values),
        "exceedances": exceedances,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-") or "variant"


def _info_offsets(info: dict[str, str | bool], key: str) -> list[int] | None:
    value = info.get(key)
    if not isinstance(value, str):
        return None
    try:
        parsed = [int(item) for item in value.split(",")]
    except ValueError:
        return None
    return parsed if len(parsed) == 2 else None


def build_statistical_context(
    populations: list[str], sample_counts: dict[str, int], *, permutations: int,
    seed: int, variant_count: int, region: str, fdr_threshold: float, mean_fst: float,
) -> str:
    population_description = "; ".join(
        f"{population} (n={sample_counts[population]})" for population in populations
    )
    comparison_description = (
        "Exactly two populations are compared, so there is only one pair: "
        "fst_max is that pair's Fst and fst_max_pair names that sole comparison. "
        if len(populations) == 2 else
        "More than two populations are compared, so Hudson Fst is calculated for "
        "every pair; fst_max is the largest pairwise value and fst_max_pair names "
        "the pair attaining it (the first pair in case of a tie). "
    )
    return (
        f"Population groups selected from the sample panel: {population_description}. "
        "Hudson Fst is calculated using scikit-allel. "
        "With more than two populations, all pairs are compared and the largest "
        "Fst is retained for each SV. "
        + comparison_description
        + "Negative or undefined pairwise estimates are set to zero. "
        f"Keeping genotypes fixed, population labels were shuffled {permutations} "
        f"times using random seed {seed}. The empirical right-tail p-value is the "
        "proportion of permutations whose maximum pairwise Fst (the sole pair's "
        "Fst when there are two populations) is greater than or equal to the "
        f"observed value; zero p-values were replaced by 1/{permutations}. "
        f"Benjamini-Hochberg correction was applied jointly to all {variant_count} "
        f"analyzed SVs in region {region}. Candidates satisfy q < {fdr_threshold} "
        f"and maximum Fst > the analyzed-set mean ({mean_fst:.12g}). "
        "candidate_rank is the 1-based rank among all analyzed SVs, ordered by "
        f"{CANDIDATE_SORT_ORDER}; "
        "it is not the p-value rank used internally in BH correction. "
        "Top-k candidates are selected from SVs passing both thresholds in this "
        "order; candidate ranks can have gaps after filtering. "
        "The seed is a reproducibility parameter, not biological evidence. "
        "Fst measures population differentiation without indicating its direction; "
        "allele frequencies indicate direction. These statistics alone do not "
        "establish natural selection, functional effects, or pathogenicity. "
        "Each quality.call_rate_<population> is the fraction of samples in that "
        "population with both genotype alleles non-missing. Call rate alone does "
        "not establish genotyping accuracy or population-specific missingness bias; "
        "no fixed call-rate cutoff was used to select these candidates."
    )


def write_outputs(
    output_dir: Path,
    variants: list[Variant],
    genotypes: np.ndarray,
    labels: np.ndarray,
    populations: list[str],
    result: dict[str, Any],
    *,
    vcf: Path,
    panel: Path,
    region: str,
    genome_build: str,
    permutations: int,
    seed: int,
    fdr_threshold: float,
    top_k: int,
    skipped: dict[str, int],
) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"output directory is not empty: {output_dir}")
    opener = gzip.open if vcf.suffix == ".gz" else open
    with opener(vcf, "rb") as handle:
        try:
            headers = allel.read_vcf_headers(handle)
        except RuntimeError as exc:
            raise ValueError(str(exc)) from exc
    info_descriptions = {key: value["Description"] for key, value in headers.infos.items()
                         if value["Description"].strip()}
    candidates_dir = output_dir / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    mean_fst = float(np.mean(result["fst_max"]))
    statistical_context = build_statistical_context(
        populations,
        {population: int(np.count_nonzero(labels == population)) for population in populations},
        permutations=permutations, seed=seed, variant_count=len(variants),
        region=region, fdr_threshold=fdr_threshold, mean_fst=mean_fst,
    )
    significant = (result["q_value"] < fdr_threshold) & (result["fst_max"] > mean_fst)
    order = sorted(
        range(len(variants)),
        key=lambda index: (-result["fst_max"][index], result["q_value"][index], variants[index].variant_id),
    )

    ranking_fields = [
        "candidate_rank", "sv_id", "chrom", "start", "end", "sv_type", "fst_max",
        "fst_max_pair", "p_value", "q_value", "significant",
    ] + [f"fst_{name}" for name in result["pair_names"]]
    ranking_rows: list[dict[str, Any]] = []
    for candidate_rank, index in enumerate(order, start=1):
        variant = variants[index]
        row = {
            "candidate_rank": candidate_rank, "sv_id": variant.variant_id, "chrom": variant.chrom,
            "start": variant.pos, "end": variant.end, "sv_type": variant.sv_type,
            "fst_max": float(result["fst_max"][index]),
            "fst_max_pair": str(result["fst_max_pair"][index]),
            "p_value": float(result["p_value"][index]),
            "q_value": float(result["q_value"][index]),
            "significant": bool(significant[index]),
        }
        row.update({
            f"fst_{name}": float(result["pair_fst"][index, pair_index])
            for pair_index, name in enumerate(result["pair_names"])
        })
        ranking_rows.append(row)
    with (output_dir / "ranking.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ranking_fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(ranking_rows)

    manifest_cases: list[dict[str, str]] = []
    selected_indices = [index for index in order if significant[index]][:top_k]
    used_names: set[str] = set()
    for index in selected_indices:
        variant = variants[index]
        filename = _safe_name(variant.variant_id) + ".json"
        if filename in used_names:
            raise ValueError(f"candidate filename collision for {variant.variant_id}")
        used_names.add(filename)
        statistics: dict[str, Any] = {
            "fst_max": float(result["fst_max"][index]),
            "fst_max_pair": str(result["fst_max_pair"][index]),
            "p_value": float(result["p_value"][index]),
            "q_value_bh": float(result["q_value"][index]),
            "candidate_rank": order.index(index) + 1,
        }
        quality: dict[str, Any] = {"vcf_filter": variant.filter}
        for population in populations:
            group = labels == population
            group_gt = genotypes[index, group, :]
            called = np.all(group_gt >= 0, axis=1)
            alt_count = int(np.count_nonzero(group_gt == 1))
            allele_number = int(np.count_nonzero(group_gt >= 0))
            statistics[f"af_{population}"] = alt_count / allele_number if allele_number else None
            statistics[f"ac_{population}"] = alt_count
            statistics[f"an_{population}"] = allele_number
            quality[f"call_rate_{population}"] = float(np.mean(called))
        statistics.update({
            f"fst_{name}": float(result["pair_fst"][index, pair_index])
            for pair_index, name in enumerate(result["pair_names"])
        })
        candidate: dict[str, Any] = {
            "sv_id": variant.variant_id,
            "genome_build": genome_build,
            "chrom": variant.chrom,
            "start": variant.pos,
            "end": variant.end,
            "sv_type": variant.sv_type,
            "statistics": statistics,
            "statistical_context": statistical_context,
            "quality": quality,
            "source_record": {
                "dataset": "1000G-SV",
                "vcf_id": variant.variant_id,
                "ref": variant.ref,
                "alt": variant.alt,
                "filter": variant.filter,
                "INFO": variant.info,
                "info_definition": {key: info_descriptions[key] for key in variant.info
                                    if key in info_descriptions},
            },
        }
        if variant.length_bp is not None:
            candidate["length_bp"] = variant.length_bp
        for key in ("CIPOS", "CIEND"):
            offsets = _info_offsets(variant.info, key)
            if offsets is not None:
                candidate[key] = offsets
        if "IMPRECISE" in variant.info:
            candidate["IMPRECISE"] = True
        path = candidates_dir / filename
        path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest_cases.append({
            "case_id": variant.variant_id,
            "category": "fst_significant",
            "input": f"candidates/{filename}",
            "purpose": f"SG10K-style max Hudson Fst candidate ({result['fst_max_pair'][index]})",
        })

    manifest = {
        "corpus_version": "1000g-sv-fst-v1",
        "reference_build": genome_build,
        "coordinate_system": "1-based-inclusive",
        "cases": manifest_cases,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "method": "SG10K-SV max pairwise Hudson Fst with label permutation and BH-FDR",
        "region": region,
        "populations": populations,
        "population_sample_counts": {population: int(np.count_nonzero(labels == population)) for population in populations},
        "permutations": permutations,
        "seed": seed,
        "p_value_method": "right-tail count(null_fst_max >= observed_fst_max) / permutations; zero floored at 1/permutations",
        "fdr_method": "Benjamini-Hochberg",
        "fdr_threshold": fdr_threshold,
        "candidate_sort_order": CANDIDATE_SORT_ORDER,
        "top_k": top_k,
        "mean_fst": mean_fst,
        "analyzed_variant_count": len(variants),
        "significant_variant_count": int(np.count_nonzero(significant)),
        "emitted_candidate_count": len(manifest_cases),
        "skipped": skipped,
        "inputs": {
            "vcf": str(vcf.resolve()), "vcf_sha256": _sha256(vcf),
            "panel": str(panel.resolve()), "panel_sha256": _sha256(panel),
        },
    }
    (output_dir / "screening_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Screen biallelic SVs with the SG10K-SV Fst method.")
    parser.add_argument("--vcf", required=True, type=Path)
    parser.add_argument("--panel", required=True, type=Path)
    parser.add_argument("--population", action="append", required=True, dest="populations")
    parser.add_argument("--region", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--genome-build", default="GRCh38")
    parser.add_argument("--permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fdr-threshold", type=float, default=0.01)
    parser.add_argument("--top-k", type=int, default=5,
                        help="Emit up to this many eligible SVs, ordered by Fst descending, q-value ascending, then SV ID ascending.")
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        if not 0 < args.fdr_threshold <= 1:
            raise ValueError("fdr-threshold must be in (0, 1]")
        if args.top_k < 1:
            raise ValueError("top-k must be positive")
        populations = list(dict.fromkeys(args.populations))
        region = parse_region(args.region)
        panel = load_panel(args.panel, populations)
        variants, genotypes, labels, skipped = read_vcf_region(args.vcf, panel, region)
        result = calculate(
            genotypes, labels, populations,
            permutations=args.permutations, seed=args.seed,
        )
        metadata = write_outputs(
            args.output, variants, genotypes, labels, populations, result,
            vcf=args.vcf, panel=args.panel, region=args.region,
            genome_build=args.genome_build, permutations=args.permutations,
            seed=args.seed, fdr_threshold=args.fdr_threshold,
            top_k=args.top_k, skipped=skipped,
        )
    except (OSError, ValueError, csv.Error, json.JSONDecodeError) as exc:
        print(f"error: {exc}")
        return 2
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
