# SV Investigator

SV Investigator is a Google ADK prototype that investigates one pre-screened
structural variant (SV) and produces a traceable JSON and Markdown report.
It combines deterministic database tools with bounded LLM decisions. It does
not call SVs from sequencing reads and does not replace clinical or expert
review.

## Workflow

```text
Input normalization
  → fixed baseline evidence
  → bounded adaptive follow-up
  → PubMed search
  → evidence synthesis
  → claim verification
  → deterministic report assembly
```

The workflow is implemented as a Google ADK `SequentialAgent`. Tool results are
written directly to session state. Before synthesis, the program builds an
evidence view that maps each `evidence_id` to its original record. The verifier
checks claims against those records, while the final report is assembled and
validated by code.

## Quick start

Use Python 3.11 or newer:

```powershell
py -m pip install -e .
$env:GOOGLE_API_KEY="your-key"
adk web
```

Select `sv_investigator` in ADK Web and paste a candidate SV as JSON. The
example input is in [`example_input.json`](example_input.json). Set
`SV_AGENT_MODEL` to override the default model.

For a non-interactive batch run:

```powershell
sv-runner --manifest test_cases.json --output-dir runs/my-run
```

## Evidence sources

The fixed baseline queries Ensembl overlap and VEP, gnomAD-SV, ClinGen Dosage,
ClinVar, dbVar, DGV Gold Standard, and deterministic input/QC checks. The
adaptive stage can make at most two justified follow-up queries from a fixed
action list. LiteratureAgent runs at most three PubMed searches and currently
stores citation metadata rather than full-text evidence.

Database matches retain their coordinate semantics and limitations. A partial
overlap, population frequency, computational prediction, or database record
does not by itself establish causality, pathogenicity, or a clinical diagnosis.
Query failures and missing sources remain explicitly labeled rather than being
treated as negative findings.

## Reports and reference run

Each run can save the complete session state, evidence catalog, validated report,
Markdown rendering, event log, and metrics. The six-case v1.1.1 reference run
is available under [`examples/runs/v1.1.1`](examples/runs/v1.1.1); all six cases
completed with schema-valid reports.

## Repository map

- `agent.py` — ADK agents and sequential orchestration
- `prompts.py` — stage instructions
- `tools.py` — public database adapters and retry/fallback behavior
- `state_pipeline.py` — state projection, evidence catalog, and report assembly
- `schemas.py` — input, claim, verification, and report schemas
- `runner.py` — batch execution and saved run artifacts
- `architecture/` and `docs/` — field-level lineage and interactive workflow map
- `tests/` — deterministic tool and state-pipeline tests

Open [`docs/system_flow.html`](docs/system_flow.html) to inspect the interactive
field-level workflow map. Its editable source is
[`architecture/data_lineage.json`](architecture/data_lineage.json).

## Current limitations

- External APIs can time out, rate-limit, or return incomplete records.
- Ensembl overlap is spatial annotation, not a molecular consequence model.
- PubMed evidence is currently citation-metadata level unless a future tool adds
  abstract or full-text retrieval.
- Alternate contigs, liftover, inserted sequence, and comprehensive phenotype or
  functional databases are outside the current MVP.
- Final interpretations require human review, especially for clinical use.
