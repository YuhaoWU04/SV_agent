# SV Investigator (Google ADK)

Current prototype release: **v1.1.1**.

The current six-case v1.1.1 reference run is stored in
[`examples/runs/v1.1.1`](examples/runs/v1.1.1). It was generated with
`gemini-3.1-flash-lite` and includes complete session state, validated reports,
Markdown renderings, compact event logs, and aggregate metrics. The older v1.0.0
reference remains in [`examples/runs/v1.0.0`](examples/runs/v1.0.0).

This is a research prototype for investigating one pre-screened structural
variant. It does not call SVs from reads and does not replace expert review.

## Workflow

`InputNormalizerAgent → BaselineEvidenceCollectorAgent →
AdaptiveInvestigationAgent → LiteratureAgent → EvidenceSynthesisAgent →
EvidenceVerifierAgent → ReportAssemblyAgent`

The root is a Google ADK `SequentialAgent`. Tool wrappers write complete normalized,
baseline, adaptive, and PubMed results directly to `ToolContext.state`; these raw
records are not saved from the model's retelling. The adaptive and literature agents'
`output_key` values contain compact query decisions and audits, while synthesis and
verification have no tools and enforce Pydantic output schemas. The final
`ReportAssemblyAgent` is deterministic and makes no model call. The design is a
deterministic baseline plus bounded adaptation: Ensembl overlap/VEP,
gnomAD-SV, ClinGen Dosage, ClinVar, dbVar, DGV Gold Standard, and artifact checks
always run, after which one LLM stage may make
zero, one, or two justified calls from a hard-coded whitelist. Missing evidence remains
`unknown`, `not_found`, `not_applicable`, `unavailable`, `error`, or `not_queried`
rather than being silently treated as negative evidence.

Synthesis assigns every atomic claim a report section, and the verifier judges its
exact wording. A callback binds verdicts back to the original claim fields so the
verifier cannot rewrite them. `ReportAssemblyAgent` then admits only exactly supported
claims into those sections, derives status and next steps, builds provenance and the
evidence catalog, and validates the result as `SVReport`. Partially supported claims
remain visible with their qualifications instead of becoming unqualified prose.

The raw state keys are `normalized_sv`, `baseline_evidence`,
`adaptive_tool_results`, and `literature_tool_results`. Immediately before synthesis,
a deterministic callback builds `evidence_view`: `records_by_id` maps every real
evidence ID to the exact tool-owned record, while `source_context` retains status,
errors, counts, limitations, and query audits without repeating those records. The
complete raw state is still preserved for audit. Synthesis, verification, and report
agents use `include_contents="none"` and receive only explicitly injected state, so
earlier tool responses are not replayed into each prompt. This reduces repeated prompt
content. Before verification the same view is narrowed to IDs cited by candidate
claims, so unrelated records are not sent again. Adaptive and literature summaries
are not replayed into synthesis; it reads tool-owned records directly. This does not
reduce saved raw state size or make semantic support judgment deterministic.

## Interactive architecture map

Open [`docs/system_flow.html`](docs/system_flow.html) in a browser for the complete
field-level behavior map. It combines each agent and its tool into one human-facing
stage. You can pan and zoom the canvas, search field names or meanings, and click any
field or operation to highlight its directly connected inputs, transformation rule,
and outputs. The **追踪完整上下游** switch expands the selection to the whole lineage;
**显示全部字段连线** reveals the full graph as faint context. Lines attach to node
edges, with same-stage links routed through the card gutter. The detail panel shows
missing-value behavior and implementation location.

The editable source is `architecture/data_lineage.json`; the generated field reference
is [`docs/field_dictionary.md`](docs/field_dictionary.md). After changing an agent,
prompt, tool, schema, configuration value, or field, regenerate and verify the map:

```powershell
py sv_investigator/scripts/generate_flow_diagram.py
py sv_investigator/scripts/generate_flow_diagram.py --check
```

See [`architecture/README.md`](architecture/README.md) for the maintenance contract.

## Install and run

Use Python 3.11 or newer in a virtual environment:

```powershell
py -m pip install -e sv_investigator
$env:GOOGLE_API_KEY="your-key"
adk web
```

Select `sv_investigator` in the ADK web interface and paste the contents of
`sv_investigator/example_input.json` as the user message. Change the model with
`SV_AGENT_MODEL` if required.

## InputNormalizerAgent: current capability and limitations

Coordinates use the VCF convention: **1-based, inclusive at both ends**. Therefore,
an interval's reference span is `end - start + 1`. The normalizer rejects non-integer,
zero, negative, reversed, and out-of-chromosome coordinates. Chromosome bounds are
checked against the primary chromosomes of the selected reference assembly; alternate
contigs and patches are not currently accepted.

Reference-build aliases are case-insensitive. `hg19`, `b37`, `build37`, and GRCh37
patch labels normalize to `GRCh37`; `hg38`, `b38`, `build38`, and GRCh38 patch labels
normalize to `GRCh38`. The original value is retained in `genome_build_original`.

Canonical SV types are `DEL`, `DUP`, `INV`, `INS`, `BND`, and `CNV`. Common labels
such as `deletion`, `loss`, `gain`, `translocation`, and mobile-element labels are
normalized automatically. `ALU`, `LINE`/`LINE1`/`L1`, `SVA`, and `MEI` become `INS`,
while the more specific class is retained in `sv_subtype`. Original values and every
normalization are retained for audit in `sv_type_original` and `normalizations`.

Primary chromosome lengths come from the Genome Reference Consortium's GRCh37 and
GRCh38 assembly data. The coordinate convention follows the VCF specification.

The normalizer is deterministic: it validates and canonicalizes supplied values but
does not infer missing coordinates, build, SV type, genotype, or quality information.
It currently accepts only primary chromosomes 1-22, X, Y, and MT. Alternate loci,
decoy contigs, non-human assemblies, liftover between builds, inserted sequence, and
copy number are not represented. A valid
normalized record therefore means that the input is structurally acceptable, not that
the SV call is biologically or technically correct.

For BND input, the original required fields remain unchanged. The normalizer
additionally recognizes a mate from any of the four standard bracketed VCF `ALT`
forms, or from `mate_chrom`/`mate_pos` and the aliases `chrom2`/`pos2`. `CHR2` plus
`END` is also accepted. It retains the two adjacency orientations parsed from `ALT`.
`CIMATE`, when supplied, describes the mate confidence interval; otherwise `CIEND` is
used for the mate. Invalid or incomplete optional mate metadata is ignored with an
explicit warning, so legacy first-breakend-only BND input remains valid. This tolerant
fallback is for compatibility and must not be mistaken for a complete BND description.

VCF breakpoint uncertainty is retained when supplied. `CIPOS` and `CIEND` may be
two-element integer arrays or comma-separated integer offsets, either at the top level
or under `source_record.INFO`; `IMPRECISE` is also retained. The normalizer stores both
the original offsets and build-bounded absolute confidence intervals. It labels
uncertainty as `complete`, `partial`, or `not_provided`. If the VCF has no `CIPOS` or
`CIEND`, omit those fields or pass `null`; do not substitute `[0, 0]`, which asserts a
zero-width interval at the reported coordinate. When a confidence interval is missing,
downstream tools use a configurable fallback window (500 bp by default, controlled by
`SV_AGENT_BREAKPOINT_TOLERANCE_BP`) to retrieve nearby candidates. This fallback is
explicitly marked as heuristic and cannot by itself make a non-exact gnomAD-SV record
`high_similarity`; measured confidence intervals or exact coordinates are required
for that label. Other overlap-based similarity classes can still apply.

## BaselineEvidenceCollectorAgent: fixed coverage

This stage calls one deterministic wrapper exactly once. The wrapper always performs
Ensembl region/breakpoint and VEP queries, build-matched gnomAD-SV, ClinGen Dosage,
ClinVar, dbVar, DGV Gold Standard, and the artifact-risk rules. Independent remote
sources run concurrently, but each result keeps its own success, partial-failure, or
error state.
The LLM wrapper cannot choose which baseline source to skip. Raw source fields are
preserved or deterministically compacted, while stable `ENS-BL-*`, `VEP-BL-*`,
`GNO-BL-*`, `CGD-BL-*`, `CLV-BL-*`, `DBV-BL-*`, and `DGV-BL-*` evidence IDs are
added. Candidate identity
fields are copied into an immutable-field audit block.

Non-Ensembl adapters use the shared `SV_AGENT_HTTP_TIMEOUT` setting (20 seconds by
default) and currently make one attempt per endpoint. Ensembl overlap and VEP share
the Ensembl-specific timeout, retry policy, and process-wide concurrency gate. A
failure is stored as `error`, never as an empty or negative result. Each source returns
at most `SV_AGENT_MAX_DATABASE_RECORDS` ranked records (10 by default), while retaining
pre-limit counts and a truncation flag.

## Baseline Ensembl annotation: capability and limitations

The region stage uses only the Ensembl REST API. For each coordinate scope it first
combines `gene`, `regulatory`, and `repeat` in one overlap request. If that request
fails, the adapter retries each feature serially so successful feature types are still
retained. It returns the normalized
build, region, and SV type for provenance, but the overlap operation itself is not
SV-type-aware: the same interval produces the same overlap features for DEL, DUP,
INV, INS, BND, and CNV. These results support statements such as "the interval overlaps
this Ensembl feature" only; they do not establish a molecular consequence, dosage
effect, phenotype, pathogenicity, or causal mechanism.

Each feature type is capped at `SV_AGENT_MAX_DATABASE_RECORDS` records (10 by default),
and the response reports whether truncation occurred. Feature lists are separated
after retrieval:
an empty list means a successful query with no records, while `null` means that query
failed. `completeness` is `complete`, `partial`, or `failed`; a partially failed query
must not be interpreted as comprehensive absence. The same features are also queried
separately around the start and end breakpoint windows. These results are labelled by
whether the window came from VCF confidence intervals or from the heuristic fallback;
features found only in a fallback window are nearby candidates, not confirmed SV
overlaps.

Ensembl requests have a 60-second timeout and at most four attempts by default. All
Ensembl overlap, VEP, and adaptive requests are process-wide serialized and share an
exponential cooldown starting at five seconds, with up to 25% random jitter. Only
timeouts, connection errors, HTTP 429,
and HTTP 500/502/503/504 are retried; other HTTP errors and malformed responses are
not. `attempts` records the total combined and fallback attempts relevant to each
feature, or the attempts for VEP/adaptive queries. Exhausted retries remain explicit errors,
not empty annotation results. These defaults can be changed with
`SV_AGENT_ENSEMBL_HTTP_TIMEOUT`, `SV_AGENT_ENSEMBL_MAX_ATTEMPTS`, and
`SV_AGENT_ENSEMBL_RETRY_BACKOFF`.

This spatial-overlap adapter does not provide transcript, exon, CDS, MANE transcript,
protein consequence, or affected-feature percentage; those are handled separately by
the bounded VEP adapter below. The baseline still does not provide nearest genes,
enhancer-gene links, conservation, segmental duplication, curated RepeatMasker, or
mappability tracks. It
also does not split intervals that exceed the Ensembl overlap endpoint's region-size
limit, and it records the retrieval time but not a pinned Ensembl release. Repeat
overlap across a large SV is only a coarse observation and must not be treated as proof
that either breakpoint is unreliable.

## Baseline Ensembl VEP consequence query

The VEP adapter submits the normalized build, interval, strand, and symbolic `DEL`,
`DUP`, `INV`, or `INS` allele to the official
[Ensembl VEP region endpoint](https://rest.ensembl.org/documentation/info/vep_region_get).
Point insertions are translated to VEP's between-base `start=end+1` representation
without changing the normalized coordinates used by other tools.
It retains the input-level most-severe consequence and a ranked, compact set of
transcript, regulatory, motif, and intergenic consequences. Transcript records can
include gene/transcript IDs, symbols, biotype, canonical and MANE flags, exon/intron
number, overlap amount, consequence terms, and impact.

VEP is not called for BND because the single-region endpoint cannot represent and
verify the full adjacency, or for direction-unknown `CNV` because deletion and
duplication consequences differ. Intervals larger than
`SV_AGENT_MAX_VEP_INTERVAL_BP` (5 Mb by default) return `not_applicable` to avoid an
unbounded, failure-prone request. VEP output is a prediction for the submitted symbolic
allele, not experimental validation, expression evidence, dosage classification, or a
patient-level conclusion. The response is capped and the Ensembl release is not pinned.

## Baseline gnomAD-SV query and matching

The population baseline queries the public gnomAD GraphQL API directly. GRCh38 input
uses `gnomad_sv_r4`; GRCh37 input uses `gnomad_sv_r2_1`. The
tool returns build-matched gnomAD-SV records with coordinates, SV type, allele count,
allele number, allele frequency, homozygote/hemizygote counts, consequence, and filter
flags.

Candidate matching is deterministic. Incompatible SV types are excluded. DEL, DUP,
INV, and CNV candidates are compared using both signed breakpoint offsets, size similarity,
and reciprocal overlap. INS is compared around the insertion point. For BND input with
a parsed mate, the tool queries both breakpoint windows and compares the chromosome
pair and both positions; reversed database breakend order is accepted. Input adjacency
orientation is retained, but the current gnomAD response does not expose an orientation
field to compare against it. If the mate is absent, the tool preserves the legacy
first-breakend-only search, labels its scope explicitly, and never treats an exact first
coordinate as proof of the same BND event. Matches are labelled `exact`, `high_similarity`,
`partial_overlap`, `region_overlap`, or `nearby`; only `exact` establishes identical
coordinates. Every non-exact record remains a candidate and includes the metrics and
uncertainty-window source used for classification.

Interval records expose signed `start_offset_bp` and `end_offset_bp`, calculated as
`database coordinate - input coordinate`. Negative values place the database
breakpoint to the left of the input; positive values place it to the right. Ranking
uses their absolute magnitudes, so this representation change does not alter candidate
ordering or similarity classes.

For intervals up to 5 Mb, the tool searches the expanded full interval. For larger SVs,
it queries the two breakpoint windows separately to keep the public region request
bounded, then merges duplicate records. Results are capped at
`SV_AGENT_MAX_DATABASE_RECORDS` after ranking. No result in gnomAD-SV does not prove
novelty, pathogenicity, or technical validity.

gnomAD-SV remains the primary frequency source, but it is no longer the only population
database: DGV Gold Standard is also queried as described below. The prompts still
forbid invented results from OMIM, GWAS Catalog, GO, Reactome, or model memory.

The GraphQL endpoint is the public gnomAD Browser's browser-facing API rather than a
versioned contract maintained specifically for this project. Dataset IDs are pinned,
but an upstream API schema change may require an adapter update and must be reported as
an error rather than interpreted as no matching variants.

## Baseline ClinGen Dosage query

For `DEL`, `DUP`, and `CNV`, the tool downloads ClinGen's
[current combined gene/region dosage-curation CSV](https://search.clinicalgenome.org/kb/downloads)
and intersects the build-matched coordinates. A deletion selects
haploinsufficiency as the relevant direction, a duplication selects
triplosensitivity, and an unspecified CNV retains both. Results include the HGNC/ISCA
identifier, entity type, coordinates, both assessments and normalized score when the
standard ClinGen label maps to 0/1/2/3/30/40, curation date, report URL, reciprocal
overlap, and breakpoint distances. Curated regions are ranked before individual genes
so a recurrent-region result is not hidden by many overlapping gene records. Other SV
types return `not_applicable` rather than a misleading negative result.

ClinGen evidence is region- or gene-level dosage evidence, not a patient-specific
classification. Matching coordinates do not prove the same recurrent breakpoints,
absolute copy number, structural configuration, phenotype, inheritance, penetrance,
or expressivity. The live combined CSV is not pinned to a historical release, so each
result records the file creation date and retrieval time.

## Baseline ClinVar query

The ClinVar adapter uses [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/)
with a build-specific coordinate field,
compatible structural-variant type, and a minimum 50 bp variant-length filter (except
for BND/translocation searches). It fetches aggregate VCV summaries and retains the
Variation ID, accession version, displayed GRCh coordinates, any inner/outer bounds,
classification, review status, last evaluation, conditions, genes, and counts of SCV
and RCV support. It never converts an exact displayed-coordinate match into proof that
two biological events are identical.

ClinVar contains submitted interpretations with unequal review status and possible
conflicts. A pathogenic label with no assertion criteria is not equivalent to an
expert-panel-reviewed record. The bounded E-utilities search can be truncated, large
SVs use separate breakpoint regions, and absence from the returned records does not
prove novelty or benignity. Configure `NCBI_EMAIL` and optionally `NCBI_API_KEY` for
NCBI requests.

ClinVar, dbVar, and PubMed share a process-wide E-utilities rate limiter. Requests are
serialized at approximately three per second without `NCBI_API_KEY`, or ten per second
when a key is configured, so concurrently scheduled baseline sources do not exceed
NCBI's documented usage rate.

## Baseline dbVar query

The dbVar adapter uses NCBI ESearch and ESummary following the official
[dbVar Entrez access method](https://www.ncbi.nlm.nih.gov/dbvar/content/tools/entrez/).
It searches the candidate or bounded breakpoint regions by chromosome, endpoints,
object type, and compatible structural-variant type, then filters the returned
placements to the requested GRCh build. Records include the dbVar variant and study
accessions, placement assembly, reported variant types, methods, genes, publications,
clinical-significance strings when supplied, variant-call count, and deterministic
coordinate match metrics.

dbVar aggregates heterogeneous submitter-defined variant regions and calls. A generic
`copy number variation` record is retained for DEL/DUP only with
`type_compatibility=ambiguous_cnv_direction`; it is not silently treated as a
direction-confirmed match. BND returns `not_applicable` because ESummary does not expose
a reliable two-breakend adjacency for comparison. The bounded endpoint search may miss
a much larger record that completely encloses the query without placing either dbVar
endpoint inside it, and ESearch may truncate before all candidates are summarized.
Remapped coordinates and exact displayed coordinates therefore remain contextual
evidence, not proof of event identity, validation, or clinical significance.

## Baseline DGV query

The DGV adapter queries the `dgvGold` GRCh37/GRCh38 track through the
[UCSC public API](https://genome.ucsc.edu/goldenPath/help/api.html), while the
[DGV downloads page](https://dgv.tcag.ca/dgv/app/downloads) remains the provenance
link for the complete source database.
It converts UCSC's 0-based half-open coordinates back to the project's 1-based
inclusive convention, filters compatible types, calculates the same deterministic
overlap metrics, and returns compact records. Frequencies, tested/observed sample
counts, study and platform counts, and short capped identifier lists are retained;
the potentially enormous full sample and supporting-variant lists are deliberately
not copied into ADK state.

This is the curated **DGV Gold Standard track**, not the complete current DGV release.
DGV combines healthy-control studies with heterogeneous technologies and often
imprecise boundaries, so overlap and population frequency are contextual evidence,
not automatic benign classification or proof of event identity. BND returns
`not_applicable`. Large intervals use separate breakpoint queries, and results are
capped by `SV_AGENT_MAX_DATABASE_RECORDS`.

## AdaptiveInvestigationAgent: bounded freedom

The adaptive stage reads the complete baseline, names evidence gaps, and may choose at
most two non-duplicate actions. The limit and duplicate check are enforced in ADK
session state by the tool, not merely requested in the prompt. Every attempted action
records its evidence gap, reason, expected information gain, status, and any rejection.
An external failure consumes a slot, preventing unbounded retries.

The implemented whitelist is deliberately smaller than the conceptual roadmap:

- Ensembl genes within 10 kb or 50 kb, ranked by coordinate distance;
- Ensembl transcript or exon overlaps;
- transcript overlap at a parsed BND mate;
- gnomAD-SV retrieval expanded by 2 kb or 10 kb.

An expanded gnomAD request changes only which records are retrieved. The original VCF
confidence intervals remain the measured matching windows; when CI is absent, the
declared fallback expands retrieval only and does not by itself confer
`high_similarity`. Thus a newly retrieved distant record cannot be promoted simply
because the search radius was widened.

Ensembl VEP, ClinGen Dosage, ClinVar, dbVar, and DGV are mandatory baseline sources,
not adaptive actions; the agent must use their stored results rather than spend its
two calls repeating them. The complete current DGV release, OMIM, phenotype matching,
enhancer-gene linking, and other regulatory-effect resources remain unavailable. The
agent must stop or record those limitations
rather than simulate a query from model knowledge. Transcript/exon actions remain
coordinate-overlap observations and do not predict molecular consequence.

The stage makes no call unless a named evidence gap, a relevant available action,
remaining budget, non-duplication, and plausible effect on interpretation or next
steps are all present. Zero adaptive calls is a valid completed decision, not agent
inactivity. Its plan, actions, stop reason, and remaining limitations are copied into
the report's required `investigation_log`.

## LiteratureAgent: bounded PubMed lookup

The tool enforces at most three distinct PubMed searches per investigation; the
limit is not prompt-only. Query deduplication ignores letter case and repeated
whitespace. Each completed search, including an API error, consumes one slot;
duplicate or over-budget requests are rejected without another API call. By default
each search returns at most five records (`SV_AGENT_MAX_PUBMED_RECORDS`), and PMIDs
already returned by an earlier search are removed from later results. Consequently
the default maximum is 15 distinct citations, often fewer after deduplication.
Records retain only the first three author names plus `author_count` and
`authors_truncated`; full author objects are not needed for the current metadata-level
investigation. Titles and metadata remain contextual rather than mechanistic proof.
Coordinate searches must keep the exact locus and SV type; the agent may not broaden
a small event into a cytoband-, chromosome-arm-, syndrome-, or generic-deletion query.

NCBI recommends identifying API clients used for PubMed. Set `NCBI_EMAIL` and
optionally `NCBI_API_KEY`.

## EvidenceSynthesisAgent and EvidenceVerifierAgent

These are separate roles. `EvidenceSynthesisAgent` reads the normalized candidate and
the deterministic `evidence_view`, then emits atomic `CandidateClaim` objects. It does
not emit a second free-text summary because that would duplicate and potentially
amplify the same claims. Factual candidates must carry evidence IDs; the synthesis
stage does not decide whether its own wording is adequately supported.

`EvidenceVerifierAgent` receives those candidates plus the same ID-to-record view. It
must preserve each candidate's ID and text, inspect the actual cited records, and mark
the claim supported, partially supported, unsupported, or conflicting. It may not add
new claims. ID lookup and record integrity are deterministic; scientific entailment,
overinterpretation checks, and conflict assessment remain model judgments and still
require expert review for consequential use.

The program applies conservative floors after model verification: hypotheses
cannot become established findings; claims supported only by PubMed citation metadata
remain partially supported until the underlying paper is checked; and wording that
asserts variant identity cannot be fully supported by records lacking an exact or
high-similarity match. Inference-level benign/pathogenic or no-effect conclusions are
also qualified because this prototype is not a clinical classifier. These claims stay
visible under qualified findings rather than being discarded or promoted into the
main narrative.

The deterministic final ADK response is structured JSON. Save it and render a review
copy with:

```powershell
py -m sv_investigator.render_report report.json -o report.md
```

The evidence catalog is also assembled deterministically; it does not require another
model call. `retrieval_status` says whether the source record was retrieved, while
`finding_status` describes what that record reports (for example, a QC risk may be
`present`, `absent`, or `unknown`). Each entry contains a source-aware short summary,
a small `key_facts` object, and `used_by` paths showing which report items cite it.
Full source records remain in session state and are not duplicated into the catalog.
The Markdown renderer groups entries by source and omits empty audit fields.

## Batch runner

`runner` executes a case manifest end to end. Every case gets an independent ADK
session and is run sequentially so API failures, rate limits, and saved state remain
easy to attribute. A failed or timed-out case is recorded and the next case still
runs unless `--fail-fast` is supplied.

Only the file named by a case's `input` field is sent to the agent. The runner does
not load or expose the corpus's `expected` or `provenance` documents to the model.
It records operational and structural facts (for example schema validity, source
statuses, state size, event count, token counts, and elapsed time); it does not score
whether a biological claim is scientifically correct.

List the built-in cases without calling a model:

```powershell
py -m sv_investigator.runner --list
```

Run the full corpus, or select cases by ID or category:

```powershell
py -m sv_investigator.runner
py -m sv_investigator.runner --case giab_cmrg_del_chr4_1092990_1093039
py -m sv_investigator.runner --category technical_benchmark
```

After an editable/package install, the equivalent short command is `sv-runner`.
The model is selected by `SV_AGENT_MODEL`; the cost-oriented prototype default is
`gemini-3.1-flash-lite`. The runner loads the package-local `.env`
without overriding variables already present in the process environment, matching
the usual ADK Web setup. Useful controls include:

```powershell
sv-runner --case-timeout 900 --save-events full
sv-runner --run-dir runs/<run-name> --resume
sv-runner --run-dir runs/<run-name> --rerun-completed
```

`--resume` skips cases whose saved `metrics.json` has `run_status=complete` and
retries incomplete cases. `--rerun-completed` reruns every selected case in the
explicit run directory. Event saving can be `full` (default), `summary`, or `none`.
Generated `runs/` directories are ignored by Git.

Each run contains `run_manifest.json`, `summary.json`, and `summary.tsv`. Each case
directory contains the exact `input.json`, final `state.json`, `final_response.txt`,
`metrics.json`, and, when available, `events.jsonl`, validated `final_report.json`,
and the human-readable `report.md`. Failures additionally contain `error.json` with
the exception and traceback. A valid but intentionally `incomplete` or `blocked`
SV report still has runner status `complete`; `report_status` records that scientific
distinction separately.

## Test

```powershell
py -m unittest discover -s sv_investigator/tests
py sv_investigator/scripts/generate_flow_diagram.py --check
```

The included tests are offline. Network adapters should be evaluated separately with
recorded fixtures so database changes do not make the core test suite nondeterministic.

## MVP limitations

- Live adapters: Ensembl region/breakpoint overlap and VEP, gnomAD-SV, ClinGen Dosage,
  ClinVar, dbVar, DGV Gold, and PubMed metadata; adaptive Ensembl
  transcript/exon/nearest-gene overlap and bounded gnomAD retrieval expansion reuse
  those same public adapters.
- The complete DGV release, OMIM, phenotype ontology/matching, enhancer-gene linking,
  GWAS Catalog, GO, and Reactome are not available to the agents.
- gnomAD-SV similarity labels are screening categories and do not prove that records
  represent the same biological event.
- PubMed metadata is contextual and does not prove a paper supports a mechanism.
- Repeat data from Ensembl is a first pass; curated repeat and mappability tracks are
  still needed for production artifact assessment.
