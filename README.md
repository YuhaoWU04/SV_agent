# SV Investigator (Google ADK)

This is an early research prototype for investigating one pre-screened structural
variant. It does not call SVs from reads and does not replace expert review.

## Workflow

`InputNormalizerAgent → BaselineEvidenceCollectorAgent →
AdaptiveInvestigationAgent → LiteratureAndFunctionAgent → EvidenceVerifierAgent →
ReportWriterAgent`

The root is a Google ADK `SequentialAgent`. Tool wrappers write complete normalized,
baseline, adaptive, and PubMed results directly to `ToolContext.state`; these raw
records are not saved from the model's retelling. The adaptive and literature agents'
`output_key` values contain their decisions and interpretations, while the verifier
and writer have no tools and enforce Pydantic output schemas. The design is a
deterministic baseline plus bounded adaptation: baseline Ensembl, gnomAD-SV, ClinGen
Dosage, ClinVar, DGV Gold Standard, and artifact checks always run, after which one LLM stage may make
zero, one, or two justified calls from a hard-coded whitelist. Missing evidence remains
`unknown`, `not_found`, `unavailable`, `error`, or `not_queried` rather than being
silently treated as negative evidence.

The raw state keys are `normalized_sv`, `baseline_evidence`,
`adaptive_tool_results`, and `literature_tool_results`. Later agents currently read
the complete raw results, not compact summaries. Direct state storage protects record
integrity but **does not reduce prompt length**; a separate summary/projection step
would be needed for that, and is not implemented here.

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
Ensembl region/breakpoint queries, build-matched gnomAD-SV, ClinGen Dosage, ClinVar,
DGV Gold Standard, and the artifact-risk rules. Independent remote sources run
concurrently, but each result keeps its own success, partial-failure, or error state.
The LLM wrapper cannot choose which baseline source to skip. Raw source fields are
preserved or deterministically compacted, while stable `ENS-BL-*`, `GNO-BL-*`,
`CGD-BL-*`, `CLV-BL-*`, and `DGV-BL-*` evidence IDs are added. Candidate identity
fields are copied into an immutable-field audit block.

The three new adapters use the shared `SV_AGENT_HTTP_TIMEOUT` setting (20 seconds by
default) and currently make one attempt per endpoint; unlike Ensembl, they do not yet
retry transient HTTP failures. Such a failure is stored as `error`, never as an empty
or negative result. Each source returns at most `SV_AGENT_MAX_DATABASE_RECORDS`
ranked records (10 by default), while retaining pre-limit counts and a truncation flag.

## Baseline Ensembl annotation: capability and limitations

The region stage uses only the Ensembl REST API. It performs three coordinate-overlap
queries for `gene`, `regulatory`, and `repeat` features. It returns the normalized
build, region, and SV type for provenance, but the overlap operation itself is not
SV-type-aware: the same interval produces the same overlap features for DEL, DUP,
INV, INS, BND, and CNV. These results support statements such as "the interval overlaps
this Ensembl feature" only; they do not establish a molecular consequence, dosage
effect, phenotype, pathogenicity, or causal mechanism.

Each feature type is capped at `SV_AGENT_MAX_DATABASE_RECORDS` records (10 by default),
and the response reports whether truncation occurred. Feature lists are independent:
an empty list means a successful query with no records, while `null` means that query
failed. `completeness` is `complete`, `partial`, or `failed`; a partially failed query
must not be interpreted as comprehensive absence. The same features are also queried
separately around the start and end breakpoint windows. These results are labelled by
whether the window came from VCF confidence intervals or from the heuristic fallback;
features found only in a fallback window are nearby candidates, not confirmed SV
overlaps.

Ensembl requests have a 30-second timeout and at most two attempts by default, with
a one-second delay before retry. Only timeouts, connection errors, HTTP 429, and HTTP
500/502/503/504 are retried; other HTTP errors and malformed responses are
not. At most four Ensembl requests run concurrently. `attempts` records the number of
tries for each feature or adaptive query. Exhausted retries remain explicit errors,
not empty annotation results. These defaults can be changed with
`SV_AGENT_ENSEMBL_HTTP_TIMEOUT`, `SV_AGENT_ENSEMBL_MAX_ATTEMPTS`,
`SV_AGENT_ENSEMBL_MAX_CONCURRENT_REQUESTS`, and `SV_AGENT_ENSEMBL_RETRY_BACKOFF`.

The fixed baseline does not provide transcript, exon, CDS, MANE transcript,
protein consequence, VEP consequence, affected-feature percentage,
nearest genes, enhancer-gene links, conservation, segmental duplication, curated
RepeatMasker, or mappability tracks. It
also does not split intervals that exceed the Ensembl overlap endpoint's region-size
limit, and it records the retrieval time but not a pinned Ensembl release. Repeat
overlap across a large SV is only a coarse observation and must not be treated as proof
that either breakpoint is unreliable.

## Baseline gnomAD-SV query and matching

The population baseline queries the public gnomAD GraphQL API directly. GRCh38 input
uses `gnomad_sv_r4`; GRCh37 input uses `gnomad_sv_r2_1`. The
tool returns build-matched gnomAD-SV records with coordinates, SV type, allele count,
allele number, allele frequency, homozygote/hemizygote counts, consequence, and filter
flags.

Candidate matching is deterministic. Incompatible SV types are excluded. DEL, DUP,
INV, and CNV candidates are compared using both breakpoint distances, size similarity,
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

For intervals up to 5 Mb, the tool searches the expanded full interval. For larger SVs,
it queries the two breakpoint windows separately to keep the public region request
bounded, then merges duplicate records. Results are capped at
`SV_AGENT_MAX_DATABASE_RECORDS` after ranking. No result in gnomAD-SV does not prove
novelty, pathogenicity, or technical validity.

gnomAD-SV remains the primary frequency source, but it is no longer the only population
database: DGV Gold Standard is also queried as described below. The prompts still
forbid invented results from dbVar, OMIM, GWAS Catalog, GO, Reactome, or model memory.

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

ClinGen Dosage, ClinVar, and DGV are mandatory baseline sources, not adaptive actions;
the agent must use their stored results rather than spend its two calls repeating them.
VEP, dbVar, the complete current DGV release, OMIM, phenotype matching, and regulatory
effect resources remain unavailable. The agent must stop or record those limitations
rather than simulate a query from model knowledge. Transcript/exon actions remain
coordinate-overlap observations and do not predict molecular consequence.

The stage makes no call unless a named evidence gap, a relevant available action,
remaining budget, non-duplication, and plausible effect on interpretation or next
steps are all present. Zero adaptive calls is a valid completed decision, not agent
inactivity. Its plan, actions, stop reason, and remaining limitations are copied into
the report's required `investigation_log`.

## LiteratureAndFunctionAgent: bounded PubMed lookup

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

NCBI recommends identifying API clients used for PubMed. Set `NCBI_EMAIL` and
optionally `NCBI_API_KEY`.

The final ADK response is structured JSON. Save it and render a review copy with:

```powershell
py -m sv_investigator.render_report report.json -o report.md
```

## Test

```powershell
py -m unittest discover -s sv_investigator/tests
py sv_investigator/scripts/generate_flow_diagram.py --check
```

The included tests are offline. Network adapters should be evaluated separately with
recorded fixtures so database changes do not make the core test suite nondeterministic.

## MVP limitations

- Live adapters: Ensembl region/breakpoint overlap, gnomAD-SV region matching, and
  PubMed metadata; adaptive Ensembl transcript/exon/nearest-gene overlap and bounded
  gnomAD retrieval expansion reuse those same public adapters.
- ClinVar, dbVar, DGV, GWAS Catalog, GO, Reactome, and OMIM are not available to the
  database agent.
- gnomAD-SV similarity labels are screening categories and do not prove that records
  represent the same biological event.
- PubMed metadata is contextual and does not prove a paper supports a mechanism.
- Repeat data from Ensembl is a first pass; curated repeat and mappability tracks are
  still needed for production artifact assessment.
