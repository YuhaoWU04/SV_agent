"""Compare my-fst with the SG10K-SV authors' 1000G Hudson Fst code."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

import allel
import numpy as np

from sv_investigator.population_fst import calculate, parse_region, read_vcf_region


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_author_code(path: Path):
    # cyvcf2 is imported but unused by the authors' Fst implementation.
    if importlib.util.find_spec("cyvcf2") is None:
        module = types.ModuleType("cyvcf2")
        module.VCF = module.Writer = object
        sys.modules["cyvcf2"] = module
    if importlib.util.find_spec("pandas") is None:
        sys.modules["pandas"] = types.ModuleType("pandas")
    spec = importlib.util.spec_from_file_location("sg10k_1000g_fst", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load author code: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_groups(panel: Path) -> tuple[dict[str, str], dict[str, str]]:
    composite: dict[str, str] = {}
    superpop: dict[str, str] = {}
    with panel.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            sample = row["sample"]
            group = row["super_pop"]
            superpop[sample] = group
            composite[sample] = "EAS_SAS" if group in {"EAS", "SAS"} else "OTHER"
    return composite, superpop


def _write_subset(source: Path, target: Path, accepted: set[tuple[str, int, str]]) -> list[str]:
    samples: list[str] = []
    with gzip.open(source, "rt", encoding="utf-8") as reader, gzip.open(
        target, "wt", encoding="utf-8"
    ) as writer:
        for line in reader:
            if line.startswith("#"):
                writer.write(line)
                if line.startswith("#CHROM"):
                    samples = line.rstrip("\n").split("\t")[9:]
                continue
            fields = line.split("\t", 4)
            key = (fields[0].removeprefix("chr"), int(fields[1]), fields[2])
            if key in accepted:
                writer.write(line)
    return samples


def _our_raw_fst(genotypes: np.ndarray, labels: np.ndarray) -> np.ndarray:
    counts = []
    for population in ("EAS_SAS", "OTHER"):
        selected = genotypes[:, labels == population, :]
        counts.append((
            np.count_nonzero(selected == 1, axis=(1, 2)),
            np.count_nonzero(selected >= 0, axis=(1, 2)),
        ))
    from sv_investigator.population_fst import hudson_fst

    return hudson_fst(*counts[0], *counts[1])


def validate(vcf: Path, panel: Path, author_code: Path, region_text: str) -> dict[str, object]:
    groups, superpop = _sample_groups(panel)
    region = parse_region(region_text)
    variants, genotypes, labels, skipped = read_vcf_region(vcf, groups, region)
    accepted = {(v.chrom, v.pos, v.variant_id) for v in variants}

    with tempfile.TemporaryDirectory() as temporary:
        subset = Path(temporary) / "accepted.vcf.gz"
        source_samples = _write_subset(vcf, subset, accepted)
        author = _load_author_code(author_code)
        author_vcf, author_samples = author.load_data(str(subset))

    if source_samples != author_samples.tolist():
        raise AssertionError("the authors' sample sort changed genotype-column order")
    if list(author_vcf["variants/ID"]) != [v.variant_id for v in variants]:
        raise AssertionError("the two readers retained different variants or ordering")

    author_labels = np.asarray([superpop[sample] for sample in author_samples])
    author_gt = allel.GenotypeArray(author_vcf["calldata/GT"])
    first = np.flatnonzero(np.isin(author_labels, ["EAS", "SAS"]))
    second = np.flatnonzero(~np.isin(author_labels, ["EAS", "SAS"]))
    author_raw = np.asarray(author.get_hudson_fst(
        author_gt.count_alleles(subpop=first),
        author_gt.count_alleles(subpop=second),
    )).reshape(-1)

    our_raw = _our_raw_fst(genotypes, labels).reshape(-1)
    raw_equal = np.isclose(our_raw, author_raw, rtol=0, atol=1e-12, equal_nan=True)
    author_clean = np.where(np.isfinite(author_raw) & (author_raw > 0), author_raw, 0.0)
    ours = calculate(genotypes, labels, ["EAS_SAS", "OTHER"], permutations=1, seed=42)
    our_clean = ours["fst_max"]
    clean_equal = np.isclose(our_clean, author_clean, rtol=0, atol=1e-12)
    finite = np.isfinite(our_raw) & np.isfinite(author_raw)
    top_count = min(10, len(variants))
    author_top = np.argsort(-author_clean, kind="stable")[:top_count]
    our_top = np.argsort(-our_clean, kind="stable")[:top_count]

    report: dict[str, object] = {
        "status": "PASS" if raw_equal.all() and clean_equal.all() else "FAIL",
        "scope": "observed Hudson Fst only; permutation p-values are intentionally not compared",
        "comparison": "EAS+SAS vs all other 1000G superpopulations",
        "region": region_text,
        "variants_compared": len(variants),
        "samples": {
            "EAS_SAS": int(np.count_nonzero(labels == "EAS_SAS")),
            "OTHER": int(np.count_nonzero(labels == "OTHER")),
        },
        "raw_fst_mismatches": int(np.count_nonzero(~raw_equal)),
        "clean_fst_mismatches": int(np.count_nonzero(~clean_equal)),
        "max_abs_error_finite": float(np.max(np.abs(our_raw[finite] - author_raw[finite]))) if finite.any() else None,
        "top_ids_identical": [variants[i].variant_id for i in our_top] == [variants[i].variant_id for i in author_top],
        "top_ids": [variants[i].variant_id for i in our_top],
        "skipped_by_my_fst": skipped,
        "inputs": {
            "vcf": str(vcf.resolve()),
            "vcf_sha256": _sha256(vcf),
            "panel": str(panel.resolve()),
            "panel_sha256": _sha256(panel),
            "author_code": str(author_code.resolve()),
            "author_code_sha256": _sha256(author_code),
            "author_repository": "https://github.com/c-BIG/SG10K-SV-MANUSCRIPT",
            "author_commit": "1eedbb0b2338138c4a5c037ca432f8b0352054bf",
        },
    }
    if report["status"] != "PASS":
        raise AssertionError(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcf", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--author-code", type=Path, required=True)
    parser.add_argument("--region", default="chr2:1000000-3000000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.vcf, args.panel, args.author_code, args.region)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
