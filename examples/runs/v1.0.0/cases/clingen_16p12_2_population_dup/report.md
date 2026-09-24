# Structural Variant Investigation Report

**Status:** incomplete

## Variant summary

| Field | Value |
|---|---|
| SV ID | `TEST_GRCh38_16p12.2_population_region_DUP` |
| Reference build | GRCh38 |
| Position | chr16:21500755-21584256 |
| SV type | DUP |
| Coordinate system | 1-based-inclusive |
| Length | 83502 bp |
| Breakpoint uncertainty | not_provided; start CI=not provided; end CI=not provided |

## Baseline source checks

| Database or resource | Result |
|---|---|
| Ensembl | Found |
| Ensembl VEP | Query failed |
| gnomAD-SV | Found |
| ClinGen Dosage | Found |
| ClinVar | No record found |
| NCBI dbVar | Found |
| DGV Gold Standard | Found |

## Adaptive investigation

- Query budget used: 2/2
- Stop reason: The two-call adaptive inquiry budget has been fully exhausted.
- QUERY_TRANSCRIPTS — executed: The baseline Ensembl gene overlap list was truncated, and VEP timed out. It is currently unclear if any protein-coding genes or transcripts are located within the 83.5 kb duplication region (GRCh38 16:21500755-21584256), which is critical for determining the biological and clinical relevance of this variant.
- QUERY_NEAREST_GENE_50KB — executed: Since the baseline Ensembl VEP query timed out and the region overlap results only showed non-coding RNAs and pseudogenes inside the duplication, we lack proximity data for any nearby protein-coding genes (such as OTOA, which is noted in the overlapping ClinGen region) that may be located close to the breakpoints.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- Ensembl annotates the nominal interval of the duplication with non-coding and pseudogene elements including MIR3680-1, SMG1P3, and SLC7A5P2. (kind: database_fact; confidence: high; evidence: ENS-BL-NOMINAL-GENE-001, ENS-BL-NOMINAL-GENE-003, ENS-BL-NOMINAL-GENE-005)
- The end breakpoint of the duplication overlaps annotated repeat regions and regulatory elements, which can affect placement reliability. (kind: observation; confidence: high; evidence: ENS-BL-END-REPEAT-001, ENS-BL-END-REGULATORY-001, ENS-BL-END-REGULATORY-002, QC-BL-003)

## Population and variant-database evidence

- The duplication exactly matches a region curated by ClinGen as a 16p12.2 population region with no evidence for haploinsufficiency. (kind: database_fact; confidence: high; evidence: CGD-BL-001)
- High-frequency overlapping structural variant gains are documented in the DGV Gold Standard track, with some reporting frequency up to 97.29%. (kind: database_fact; confidence: high; evidence: DGV-BL-001, DGV-BL-002, DGV-BL-003, DGV-BL-004)
- gnomAD-SV database lists multiple overlapping duplications, including a highly frequent variant with an allele frequency of approximately 55.56%. (kind: database_fact; confidence: high; evidence: GNO-BL-002)

## Clinical evidence and phenotype associations

- ClinGen catalogs a nearby, partially overlapping 16p12.2 recurrent distal region associated with autosomal recessive phenotypes. (kind: database_fact; confidence: high; evidence: CGD-BL-002)

## Literature evidence

No evidence recorded.

## Possible interpretations

No evidence recorded.

## Qualified findings

- Publications PMID-21500755 and PMID-21584256 are unrelated to chromosome 16 microduplications and were retrieved because their PubMed IDs match the genomic coordinates of the SV. (evidence: PMID-21500755, PMID-21584256; qualification: Verified that these PMIDs discuss unrelated clinical and computational topics and were retrieved solely due to coincidence of coordinates with PMIDs.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- Publications describing OTOA-associated hearing loss do not provide direct phenotypic or clinical evidence for this specific duplication. (evidence: PMID-27068579, PMID-28000701, PMID-31527525, PMID-36147510, PMID-37114731; qualification: Verified that the OTOA papers describe mutations and variants associated with recessive hearing loss rather than this benign population duplication.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- This duplication is likely a benign population variant based on its high prevalence in healthy control cohorts and its curation as a population region. (evidence: CGD-BL-001, DGV-BL-003, GNO-BL-002; qualification: Verified that the high allele frequencies in healthy cohorts and ClinGen 0 HI score support benign classification.; Available evidence does not establish a clinical or functional classification.)
- The duplication is not expected to cause OTOA-associated hearing loss as it is distinct from the pathogenic recessive recurrent region containing OTOA. (evidence: CGD-BL-001, CGD-BL-002, PMID-31527525; qualification: Verified that the duplication region (ISCA-46691) is distinct from the distal recurrent region containing OTOA (ISCA-46297).; Available evidence does not establish a clinical or functional classification.)

## Artifact risks

- **low_call_rate — unknown**: Missingness can produce spurious population differences. Recommended check: Calculate call rate per cohort.
- **single_caller_support — unknown**: A call from one algorithm may reflect caller-specific bias. Recommended check: Validate with an orthogonal caller or experimental assay.
- **repeat_region — present**: Repeats in breakpoint windows can make breakpoint placement unreliable. Recommended check: Confirm both breakpoints against a curated repeat track.
- **low_mappability — unknown**: Low-mappability sequence can create ambiguous alignments. Recommended check: Intersect both breakpoints with a build-matched mappability track.
- **supporting_reads — unknown**: Weak read support increases false-positive risk. Recommended check: Review caller-specific split-read, paired-end, and depth thresholds.
- **genotype_quality — unknown**: Low or missing genotype quality weakens frequency estimates. Recommended check: Inspect genotype likelihoods and quality distributions by cohort.
- **batch_effect — unknown**: Unequal pipelines or batches can mimic population differentiation. Recommended check: Compare sequencing, coverage, and calling batches between cohorts.

## Contradictions

None recorded.

## Limitations

- Baseline Ensembl evidence is coordinate-overlap evidence.
- Ensembl VEP consequences are predictions for a symbolic SV allele, not experimental validation or a patient-level interpretation.
- Population evidence includes gnomAD-SV and the DGV Gold Standard track; the latter is not the complete current DGV release.
- dbVar evidence aggregates heterogeneous submitted studies and may include imprecise, remapped, or direction-ambiguous records.
- Clinical evidence includes ClinGen dosage curations and ClinVar aggregate records, neither of which is a patient-level diagnosis.
- Missing source data and query failures remain explicit unknown/error states.
- Heuristic breakpoint windows were used to retrieve overlapping database variants in the absence of VCF confidence intervals.
- Coincidence-based PubMed retrieval occurred where genomic start and end coordinates matched unrelated PMIDs.
- Overlapping recurrent region literature concerning OTOA does not establish clinical pathogenicity for this population variant.
- Artifact risk quality indicators flag repeat regions at the end breakpoint window, which can impact variant sizing and alignment accuracy.
- The Ensembl VEP consequence query timed out, leaving potential downstream transcript-level effects unpredicted.
- The Ensembl nearest gene within 50 kb query failed due to an HTTP 500 error, leaving the exact proximity to adjacent protein-coding genes unannotated.
- No ClinVar records were identified within the precise genomic coordinates of this structural variant.
- No peer-reviewed literature was found specifically describing duplications of the internal non-coding genes (SMG1P3, SLC7A5P2, MIR3680-1).
- Conservatively qualified claim C006: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C007: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C009: Available evidence does not establish a clinical or functional classification.
- Conservatively qualified claim C010: Available evidence does not establish a clinical or functional classification.
- Ensembl query was incomplete (found).
- Ensembl VEP query was incomplete (error).

## Recommended next steps

- Resolve evidence gap: The Ensembl VEP consequence query timed out, leaving potential downstream transcript-level effects unpredicted.
- Resolve evidence gap: The Ensembl nearest gene within 50 kb query failed due to an HTTP 500 error, leaving the exact proximity to adjacent protein-coding genes unannotated.
- Resolve evidence gap: No ClinVar records were identified within the precise genomic coordinates of this structural variant.
- Resolve evidence gap: No peer-reviewed literature was found specifically describing duplications of the internal non-coding genes (SMG1P3, SLC7A5P2, MIR3680-1).

## Evidence catalog

- **CGD-BL-001** [ClinGen Dosage; exact]: ClinGen Dosage record ISCA-46691 — https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-46691
- **CGD-BL-002** [ClinGen Dosage; region_overlap]: ClinGen Dosage record ISCA-46297 — https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-46297
- **DGV-BL-001** [DGV Gold; partial_overlap]: DGV Gold record gssvG14123 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21518369;end=21583079
- **DGV-BL-002** [DGV Gold; partial_overlap]: DGV Gold record gssvG14113 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21469823;end=21599245
- **DGV-BL-003** [DGV Gold; region_overlap]: DGV Gold record gssvG14136 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21530363;end=21558973
- **DGV-BL-004** [DGV Gold; region_overlap]: DGV Gold record gssvG14147 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21557857;end=21570813
- **ENS-BL-END-REGULATORY-001** [Ensembl; region_overlap]: enhancer
- **ENS-BL-END-REGULATORY-002** [Ensembl; region_overlap]: CTCF_binding_site
- **ENS-BL-END-REPEAT-001** [Ensembl; region_overlap]: AluJr
- **ENS-BL-NOMINAL-GENE-001** [Ensembl; region_overlap]: microRNA 3680-1 [Source:HGNC Symbol;Acc:HGNC:38989]
- **ENS-BL-NOMINAL-GENE-003** [Ensembl; region_overlap]: solute carrier family 7 member 5 pseudogene 2 [Source:HGNC Symbol;Acc:HGNC:24951]
- **ENS-BL-NOMINAL-GENE-005** [Ensembl; region_overlap]: SMG1 pseudogene 3 [Source:HGNC Symbol;Acc:HGNC:49860]
- **GNO-BL-002** [gnomAD-SV; region_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DUP_chr16_6602690e?dataset=gnomad_sv_r4
- **PMID-21500755** [PubMed; contextual]: Improving identification and documentation of pressure ulcers at an urban academic hospital. — https://pubmed.ncbi.nlm.nih.gov/21500755/
- **PMID-21584256** [PubMed; contextual]: Brainstorm: a user-friendly application for MEG/EEG analysis. — https://pubmed.ncbi.nlm.nih.gov/21584256/
- **PMID-27068579** [PubMed; contextual]: DNA Diagnostics of Hereditary Hearing Loss: A Targeted Resequencing Approach Combined with a Mutation Classification System. — https://pubmed.ncbi.nlm.nih.gov/27068579/
- **PMID-28000701** [PubMed; contextual]: The diagnostic yield of whole-exome sequencing targeting a gene panel for hearing impairment in The Netherlands. — https://pubmed.ncbi.nlm.nih.gov/28000701/
- **PMID-31527525** [PubMed; contextual]: Mid-Frequency Hearing Loss Is Characteristic Clinical Feature of OTOA-Associated Hearing Loss. — https://pubmed.ncbi.nlm.nih.gov/31527525/
- **PMID-36147510** [PubMed; contextual]: Genomic study of nonsyndromic hearing loss in unaffected individuals: Frequency of pathogenic and likely pathogenic variants in a Brazilian cohort of 2,097 genomes. — https://pubmed.ncbi.nlm.nih.gov/36147510/
- **PMID-37114731** [PubMed; contextual]: [Phenotype-genotype analysis of the autosomal recessive hereditary hearing loss caused by OTOA variations]. — https://pubmed.ncbi.nlm.nih.gov/37114731/
- **QC-BL-001** [Artifact-risk rules; contextual]: low_call_rate
- **QC-BL-002** [Artifact-risk rules; contextual]: single_caller_support
- **QC-BL-003** [Artifact-risk rules; contextual]: repeat_region
- **QC-BL-004** [Artifact-risk rules; contextual]: low_mappability
- **QC-BL-005** [Artifact-risk rules; contextual]: supporting_reads
- **QC-BL-006** [Artifact-risk rules; contextual]: genotype_quality
- **QC-BL-007** [Artifact-risk rules; contextual]: batch_effect

## Query provenance

- Ensembl: found — {"query_region": "16:21500755-21584256"}
- Ensembl VEP: error — {}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "16", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: found — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
- PubMed: found — 21500755 OR 21584256 OR gssvG14372 OR ISCA-46691
- PubMed: not_found — (SMG1P3 OR SLC7A5P2 OR MIR3680) AND (duplication OR "copy number")
- PubMed: found — OTOA AND (duplication OR "copy number")
