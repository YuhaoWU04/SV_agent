# SV Investigator test case corpus

This directory contains a small, versioned seed corpus. It is intentionally split
into two validation layers:

- `technical_benchmark`: exact HG002 GRCh38 records from the NIST/GIAB CMRG
  structural-variant benchmark. These cases test input normalization, coordinate
  preservation, SV representation, tool execution, and evidence provenance.
- `interpretation_reference`: synthetic CNVs matching complete ClinGen dosage
  sensitivity regions. These cases test whether a report distinguishes observed
  overlap from interpretation, preserves uncertainty, and avoids unsupported
  clinical claims.

## Isolation rule

Only the file under `inputs/` is supplied to the agent. The corresponding file
under `expected/` is hidden until evaluation. Source metadata are kept in
`provenance/`; they are not agent input either.

The interpretation cases are representative region-level CNVs, not patient
records and not exact individual breakpoints. Their ClinGen conclusions are
reference facts for later review. The current baseline now queries ClinGen Dosage;
success means retrieving and citing the relevant curation when available while still
not treating region overlap as a patient-level diagnosis or over-interpreting
Ensembl, population databases, or PubMed metadata.

## Coordinates

Agent inputs use the project's fixed `1-based-inclusive` convention.

- For a sequence-resolved VCF deletion, the VCF anchor base is excluded from the
  affected interval: `start = POS + 1`, `end = POS + len(REF) - 1`.
- For an insertion, `start = end = POS` denotes the insertion point after the VCF
  anchor base, while `length_bp` is the inserted sequence length.
- ClinGen region coordinates are copied as displayed on its GRCh38 pages. Their
  biological breakpoint meaning is described in the hidden expectation and
  provenance records.

Missing breakpoint confidence intervals are deliberately omitted. They must not
be replaced by `[0, 0]`, which would assert measured zero-width uncertainty.

## Running the corpus checks

The local unit test validates the manifest, JSON structure, input/output
separation, and every input with `normalize_sv_input` without calling external
services:

```powershell
python -m unittest tests.test_case_corpus
```

The corpus does not yet contain saved agent outputs or pass/fail decisions. Those
will be added after the cases have been run and manually verified.
