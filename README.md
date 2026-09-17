# SV Investigator (Google ADK)

This is an early research prototype for investigating one pre-screened structural
variant. It does not call SVs from reads and does not replace expert review.

## Workflow

`InputNormalizerAgent → RegionAnnotationAgent → DatabaseEvidenceAgent →
LiteratureAndFunctionAgent → ArtifactRiskAgent → EvidenceVerifierAgent →
ReportWriterAgent`

The root is a Google ADK `SequentialAgent`. Tool-using stages save JSON text through
`output_key`; the verifier and writer have no tools and enforce Pydantic output
schemas. Missing evidence remains `unknown`, `not_found`, `unavailable`, `error`, or
`not_queried` rather than being silently treated as negative evidence.

## Interactive architecture map

Open [`docs/system_flow.html`](docs/system_flow.html) in a browser for the complete
field-level behavior map. It combines each agent and its tool into one human-facing
stage. You can pan and zoom the canvas, search field names or meanings, and click any
field or operation to highlight its upstream inputs, transformation rule, downstream
outputs, missing-value behavior, and implementation location.

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
py -m pip install -r requirements-sv-agent.txt
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
uncertainty as `complete`, `partial`, or `not_provided`. When a confidence interval is
missing, downstream tools use a configurable fallback window (500 bp by default,
controlled by `SV_AGENT_BREAKPOINT_TOLERANCE_BP`) only to retrieve nearby candidates.
This fallback is explicitly marked as heuristic and is not presented as a measured
confidence interval.

## RegionAnnotationAgent: current capability and limitations

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

The current region stage does not provide transcript, exon, CDS, MANE transcript,
protein consequence, VEP consequence, affected-feature percentage,
nearest genes, enhancer-gene links, conservation, segmental duplication, curated
RepeatMasker, or mappability tracks. It
also does not split intervals that exceed the Ensembl overlap endpoint's region-size
limit, and it records the retrieval time but not a pinned Ensembl release. Repeat
overlap across a large SV is only a coarse observation and must not be treated as proof
that either breakpoint is unreliable.

## DatabaseEvidenceAgent: gnomAD-SV query and matching

The database stage now queries the public gnomAD GraphQL API directly. GRCh38 input
uses `gnomad_sv_r4`; GRCh37 input uses `gnomad_sv_r2_1`. ClinVar is not queried. The
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

gnomAD-SV is the only database available to this agent. The prompt forbids results
from ClinVar, dbVar, DGV, OMIM, GWAS Catalog, GO, Reactome, or model memory. If such a
source would be useful, the agent may only list it as `not_queried` with reason
`tool_not_available`; it may not claim that a query occurred. Static adapter
availability is documented here rather than queried on every run.

The GraphQL endpoint is the public gnomAD Browser's browser-facing API rather than a
versioned contract maintained specifically for this project. Dataset IDs are pinned,
but an upstream API schema change may require an adapter update and must be reported as
an error rather than interpreted as no matching variants.

NCBI recommends identifying API clients used for PubMed. Set `NCBI_EMAIL` and
optionally `NCBI_API_KEY`.

The final ADK response is structured JSON. Save it and render a review copy with:

```powershell
py -m sv_investigator.render_report report.json -o report.md
```

## Test

```powershell
py -m unittest tests/test_sv_tools.py
py sv_investigator/scripts/generate_flow_diagram.py --check
```

The included tests are offline. Network adapters should be evaluated separately with
recorded fixtures so database changes do not make the core test suite nondeterministic.

## MVP limitations

- Live adapters: Ensembl region/breakpoint overlap, gnomAD-SV region matching, and
  PubMed metadata.
- ClinVar, dbVar, DGV, GWAS Catalog, GO, Reactome, and OMIM are not available to the
  database agent.
- gnomAD-SV similarity labels are screening categories and do not prove that records
  represent the same biological event.
- PubMed metadata is contextual and does not prove a paper supports a mechanism.
- Repeat data from Ensembl is a first pass; curated repeat and mappability tracks are
  still needed for production artifact assessment.
