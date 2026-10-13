# SV Investigator

Current release: **v1.2.0**. See [CHANGELOG.md](CHANGELOG.md) for the release summary.

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
sv-runner --manifest test_cases.json --output runs/my-run
```

## Optional local models

Gemini remains the default and does not require LiteLLM. Install the local extra
in this project's Python environment (from the directory containing pyproject.toml):

```powershell
python -m pip install -e ".[local]"
$env:PYTHONUTF8="1"
$env:SV_AGENT_MODEL_BACKEND="litellm"
$env:SV_AGENT_MODEL="openai/local-model"
$env:SV_AGENT_API_BASE="http://127.0.0.1:8080/v1"
```

Start an OpenAI-compatible local server such as llama.cpp or LM Studio first;
replace `local-model` with its served model ID. Then run ADK Web or `sv-runner`
as usual. For Ollama, use `ollama_chat/qwen3:0.6b` and
`http://127.0.0.1:11434` instead. `SV_AGENT_API_KEY` defaults to the dummy value
`local`; set it if your server requires authentication. No Gemini credential
is used by the local model path. Database tools still require network access.

The model and server must support tool calling and JSON-schema output. Small
models are useful for integration checks, but their investigation quality is
not established. Start with one case before running a batch. Run artifacts
record the backend and server address alongside the model name.

For a live integration check without querying biological databases, run this
from the repository's parent with the local settings above:

```powershell
python -m sv_investigator.scripts.smoke_local_model
```

It checks actual tool execution, session-state updates and Pydantic JSON output,
and saves `output/local-model-test/smoke.json`. It forces the first tool call to
separate adapter compatibility from model planning quality; it does not replace
an end-to-end SV case run.

To switch back, unset the local settings and choose your Gemini model:

```powershell
Remove-Item Env:SV_AGENT_MODEL_BACKEND, Env:SV_AGENT_API_BASE -ErrorAction SilentlyContinue
$env:SV_AGENT_MODEL="gemini-3.5-flash"
```

Environment variables override `.env` in the batch runner. If these settings
are stored in `.env`, update that file too. Restart ADK Web after switching.

## Population Fst screening

`sv-fst-screen` implements the SG10K-SV population-differentiation workflow
upstream of the investigation agent: biallelic SVs, pairwise Hudson Fst, the
maximum pairwise Fst per SV, ancestry-label permutation, Benjamini-Hochberg
FDR, and selection by `q < 0.01` plus `fst_max` above the analyzed-set mean.
It writes `ranking.tsv`, provenance metadata, candidate JSON files, and a
runner-compatible `manifest.json`.

Eligibility requires both thresholds; investigation priority is then highest
`fst_max` first, lowest BH q-value second, and SV ID ascending last. `--top-k`
emits up to that many eligible SVs in this order. q-value is an eligibility
threshold and a tie-breaker, not the primary priority measure.
`ranking.tsv` includes all analyzed SVs in the same Fst-first order.
`candidate_rank` in the table and candidate JSON is the 1-based position in
that full ranking, not the rank within the eligible subset or the p-value rank
used internally by BH correction. Candidate ranks can therefore have gaps.
The English `statistical_context`, `screening_metadata.json` (including
`candidate_sort_order` and `top_k`), and manifest case order reflect this rule.
Previously saved outputs retain their original rule; this change does not
rewrite historical runs.

```powershell
sv-fst-screen `
  --vcf ALL.wgs.mergedSV.v8.20130502.svs.genotypes.GRCh38.vcf.gz `
  --panel integrated_call_samples_v3.20130502.ALL.panel `
  --population CEU --population YRI --population CHB `
  --region chr2:1000000-3000000 `
  --permutations 1000 --seed 42 --top-k 5 `
  --output runs/chr2-fst

sv-runner --manifest runs/chr2-fst/manifest.json --output runs/chr2-investigation
```

The released SG10K-SV Figure 4 code uses a right-tail permutation test
(`null fst_max >= observed fst_max`), floors zero p-values at `1/B`, and sets
negative or undefined pairwise Fst values to zero before taking the maximum.
This command preserves those choices and records them in
`screening_metadata.json`.

## INFO field descriptions

Fst export reads the source VCF header with scikit-allel and includes descriptions
only for INFO fields present in each candidate, under
`source_record.info_definition`. Raw `source_record.INFO` keys and values are
unchanged. Plain VCF and gzip-compressed VCF are supported.

Normalization resolves each present field deterministically: a supplied
description takes priority, then the known `1000G-SV` dictionary, then the common
VCF dictionary. Missing descriptions do not trigger LLM expansion. Dataset-specific
fields such as `MC` and `CS` are not guessed for an unknown dataset. The 1000G
fallback reproduces the mergedSV.v8 GRCh38 header; it is not a universal SV dictionary.
SV inputs without INFO require no new fields.

Supplied definitions may be strings (`"MC": "Merged calls."`) or objects with a
`description` string. Used descriptions must be non-empty strings. Normalized
definitions have this shape:

```json
"info_definition": {
  "MC": {"description": "Merged calls.", "source": "provided"},
  "NS": {"description": "Number of samples with data.", "source": "vcf_standard"}
}
```

The source labels are `provided`, `1000g_dictionary`, and `vcf_standard`.
`provided` means supplied by the caller, including upstream header extraction;
it does not authenticate caller-provided origin labels. Unknown fields remain in
INFO without an invented definition. Definitions describe field semantics, not
independent biological evidence. Synthesis receives these through `normalized_sv`;
they are not evidence-ID records and are not fetched by the stored-evidence tools.
Synthesis and verifier can call `get_info_descriptions(field_ids=["MC", "NS"])`
when an INFO abbreviation may be ambiguous or its meaning is unclear. It reads only
the current normalized SV and returns each requested raw value beside its saved
description and source. `missing_fields` identifies names absent from INFO;
`undefined_fields` identifies present fields lacking a saved description. Lookup
uses exact case-sensitive names, supports batches, and never expands from memory
or consults external databases. It is read-only and adds no query-call quota.
Calls remain in the ordinary ADK event log, not the evidence-ID read audit.
Adaptive and literature already receive the normalized input, including definitions;
they retain their existing query-selection tools. No extra input projection or
agent is introduced.

## Evidence sources

The fixed baseline queries Ensembl overlap and VEP, gnomAD-SV, ClinGen Dosage,
ClinVar, dbVar, DGV Gold Standard, ENCODE cCREs, GeneHancer target links,
GTEx molecular QTL context, reference mappability, and deterministic input/QC checks. The
adaptive stage can make at most two justified follow-up queries from a fixed
action list. LiteratureAgent runs at most three PubMed searches and currently
stores citation metadata rather than full-text evidence.

Database matches retain their coordinate semantics and limitations. A partial
overlap, population frequency, computational prediction, or database record
does not by itself establish causality, pathogenicity, or a clinical diagnosis.
Query failures and missing sources remain explicitly labeled rather than being
treated as negative findings.

Verification keeps the complete `evidence_view` in state rather than replacing it
with a cited-only subset. The verifier prompt receives `verification_evidence_view`:
a bounded discovery directory (up to 80 rows / 12,000 characters), cited IDs, source
counts, and query audit context, not all raw record bodies. Two read-only tools query
the stored evidence deterministically:

- `get_evidence_by_ids`: fetch up to eight exact IDs, optionally projecting fields
  or dotted paths (including list indices) for large records.
- `search_stored_evidence`: literal text and exact source/type/scope filters, plus
  1-based inclusive interval overlap; pages contain up to 20 directory entries and
  an explicit `next_offset`. Fetch discovered IDs to inspect their record bodies.

There is no fixed verification lookup-call quota. Identical requests return a small
`duplicate_request` response pointing to the earlier query rather than repeating
record bodies. Different pages, projections, and filters remain available. The runner's
existing per-case timeout bounds execution; external adaptive-query budgets are unchanged.
Responses are limited to 24,000 characters; oversize bodies,
unknown IDs, invalid fields, and truncation are explicit, never silent. Unique query audits
and fetched IDs are retained in state and reset for each new candidate. Claims with
unfetched cited records cannot pass verification. Additional records can reveal
missing citations or scope errors but do not silently replace the claim's references.
Failure to load a record is not database absence; negative search results describe
only the stored evidence and the actual source query scope/completeness.

Functional evidence is collected deterministically, without consuming adaptive
query budget. Records receive `CCRE-BL`, `REG-BL`, `QTL-BL`, or `MAP-BL` IDs and
enter the same synthesis, verification, and cited-evidence catalog flow as other
sources. The raw responses, source limitations, failures, and truncation stay in state.

- ENCODE4 cCRE registry (2024, GRCh38): nominal overlap, or explicitly labeled
  breakpoint windows for insertions, BNDs, and very large variants. Cell-type
  agnostic annotations do not identify the SV's functional tissue.
- GeneHancer Double Elite v2 (2019, GRCh37/38): enhancer/promoter-to-gene
  associations with their reported methods and scores. Only the regulatory endpoint
  is intersected, never the span of the connection. These are not ABC scores.
- GTEx DAP-G cis-eQTLs (GRCh38, no chrX): variant positions within the candidate
  region plus 10 kb, retaining tissue, target gene, variant PIP, and cluster PIP.
  GTEx v8 API sQTL follow-up covers at most three distinct regional eQTL variants,
  highest PIP first, retaining alleles, intron phenotype, tissue, p-value, and NES.
  This is regional molecular context, not exhaustive sQTL discovery, an exact
  SV-eQTL match, an LD analysis, or colocalization. Empty results cannot exclude
  molecular effects. The deprecated eQTL Catalogue REST API is not used.
- Mappability: both breakpoint windows (including a BND mate), 100-mers;
  Umap multi-read mappability on GRCh38 and CRG alignability on GRCh37. These
  measures are not interchangeable. Summaries retain coverage, weighted mean,
  minimum, and the fraction of measured bases below one. Uncovered bases remain
  unmeasured, not zero. No low-score threshold automatically declares an artifact;
  fully covered, uniformly unique windows clear only this reference-track risk.

Live adapter checks (no paid model calls):

```powershell
.\.venv\Scripts\python.exe scripts\smoke_functional_evidence.py <candidate.json> --output validation\functional_evidence
```

dbVar matches include bounded detail-page variant calls with submitted types,
sample/zygosity metadata, build-matched call placements, and HGVS when available.
Numeric copy numbers are returned only when explicitly reported, with their
sample/call identifiers and original field labels. Deletion, duplication, and
zygosity are not converted into an assumed numeric copy number. Detail failures
remain explicit, and genotype download links are provided when the page exposes
them; study-wide genotype files are not downloaded automatically. BND adjacency
matching remains unsupported by this dbVar adapter.
Details use sparse fields: empty CN, metadata, and truncation fields are omitted.
Unmapped columns in recognized call and build-matched placement rows are retained
as `additional_fields`; other-build rows and unassociated details are retained in
`additional_details`, not treated as matching placements. Explicit CN values that
cannot be parsed are preserved separately. Free text and linked files are not
comprehensively parsed; malformed rows and bounded results are labeled.

Call rates supplied in `quality.call_rate` or `quality.call_rate_*` are indexed
alongside input statistics as individual `INPUT-STAT-*` observations and included
in `statistical_signals` and the evidence catalog. Synthesis reads these records
through the normal evidence view. Existing statistic IDs are retained by appending
quality call-rate fields after the sorted statistics; duplicate fields already in
statistics are not added again. No call-rate or genotype-missingness risk item is
mechanically generated. Other artifact-risk rules remain unchanged.

Input statistics are `observation` claims. Synthesis and verification prompts
distinguish input observations from retrieved `database_fact` claims and from
interpretations (`inference`) or untested explanations (`hypothesis`). Before
reporting, input-only `database_fact` claims are corrected to `observation` with
an audit warning; inference and hypothesis labels are not automatically changed.

## Reports and reference run

PubMed-only claims are not automatically downgraded. The verifier checks the
actual retrieved citation content against each claim: exact metadata facts and
explicitly title-attributed summaries can be supported, whereas mechanisms,
experimental validation, and SV-specific relevance require corresponding evidence.
This verifies what the retrieved record says, not the validity of the study.

Factual narrative sections require `supported` claims. `possible_interpretations`
also admits verifier-qualified (`partially_supported`) inferences and hypotheses
with explicit qualification notes. Their verification status, claim type, and
citations are preserved; retained hypotheses are capped at
`partially_supported` / `low`. Unsupported/conflicting claims remain excluded.
Partially supported factual candidates remain in the structured report's
`verified_claims` for audit, but their text is not rendered as a finding in
Markdown. A verification-review notice lists their claim IDs. Qualified
interpretations appear only in `possible_interpretations`, without a duplicate
"Qualified findings" section.

Verification is bound back to the original synthesis claims after the verifier
agent finishes. This applies to both text JSON and ADK's `set_model_response`
tool output; raw model messages remain available in the saved event log.
Report assembly reconciles stored verdicts once and reuses them for the
investigation log, including when rebuilding an older JSON-string state.

Query provenance covers baseline, adaptive, and literature retrieval. Failed,
partial, or explicitly truncated queries make `report_status` incomplete and add a scoped
limitation; retained supported findings are still published. A successful
zero-hit query does not itself make a report incomplete. Operational source
metrics cover all eleven baseline adapters using `BASELINE_SOURCE_KEYS` in
`config.py`, also used by the provenance projection.
An explicitly pending, blocked, or errored required baseline cannot publish a
complete report merely because the verifier permits publication.

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
- PubMed evidence includes citation metadata and available abstracts, not full
  text. Missing summaries or failed abstract retrieval are labeled partial.
- GTEx regional context uses padded query intervals (10 kb on either side),
  explicitly labeled separately from the nominal SV interval. Regional QTLs do
  not establish an effect of the SV or linkage disequilibrium with it.
- Alternate contigs, liftover, inserted sequence, and comprehensive phenotype or
  functional databases are outside the current MVP.
- Final interpretations require human review, especially for clinical use.

## License

The project code is released under the [MIT License](LICENSE). External database
records and annotations remain subject to their respective providers' terms and
citation requirements; this license does not relicense those sources.
