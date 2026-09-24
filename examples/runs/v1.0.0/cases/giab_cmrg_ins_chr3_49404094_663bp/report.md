# Structural Variant Investigation Report

**Status:** incomplete

## Variant summary

| Field | Value |
|---|---|
| SV ID | `GIAB_CMRG_GRCh38_chr3_49404094_INS663` |
| Reference build | GRCh38 |
| Position | chr3:49404094-49404094 |
| SV type | INS |
| Coordinate system | 1-based-inclusive |
| Length | 663 bp |
| Breakpoint uncertainty | not_provided; start CI=not provided; end CI=not provided |

## Baseline source checks

| Database or resource | Result |
|---|---|
| Ensembl | Query failed |
| Ensembl VEP | Query failed |
| gnomAD-SV | Found |
| ClinGen Dosage | Not applicable |
| ClinVar | No record found |
| NCBI dbVar | Found |
| DGV Gold Standard | No record found |

## Adaptive investigation

- Query budget used: 2/2
- Stop reason: budget_exhausted
- QUERY_NEAREST_GENE_10KB — executed: Ensembl spatial overlap queries failed with HTTP 500 errors, leaving a gap in understanding which genes are located near the insertion point. dbVar records suggest RHOA is nearby, but this needs formal gene annotation.
- QUERY_TRANSCRIPTS — executed: The insertion 3:49404094 lies within the genomic span of RHOA and ENSG00000290318, but the exact transcript isoforms and whether the insertion is exonic or intronic remains unconfirmed due to earlier baseline VEP and Ensembl overlap query failures.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The coordinate of the 663 bp insertion (3:49404094, GRCh38) overlaps the genomic span of the RHOA gene (ENSG00000067560) and the novel protein gene ENSG00000290318. (kind: database_fact; confidence: high; evidence: ENS-ADP-EXPANDED_REGION-GENE-001, ENS-ADP-EXPANDED_REGION-GENE-003)
- The insertion at 3:49404094 is located 8,118 bp away from the protein-coding gene TCTA (ENSG00000145022). (kind: database_fact; confidence: high; evidence: ENS-ADP-EXPANDED_REGION-GENE-002)
- The insertion coordinate 3:49404094 falls within the genomic span of multiple ENST transcript models of RHOA, including the canonical transcript ENST00000418115. (kind: database_fact; confidence: high; evidence: ENS-ADP-NOMINAL-TRANSCRIPT-001, ENS-ADP-NOMINAL-TRANSCRIPT-002, ENS-ADP-NOMINAL-TRANSCRIPT-003, ENS-ADP-NOMINAL-TRANSCRIPT-004, ENS-ADP-NOMINAL-TRANSCRIPT-005, ENS-ADP-NOMINAL-TRANSCRIPT-006, ENS-ADP-NOMINAL-TRANSCRIPT-007, ENS-ADP-NOMINAL-TRANSCRIPT-008, ENS-ADP-NOMINAL-TRANSCRIPT-009, ENS-ADP-NOMINAL-TRANSCRIPT-010)

## Population and variant-database evidence

- A high-similarity gnomAD-SV candidate INS_chr3_9224a6a5 is reported at chromosome 3:49404094-49404095 with a length of 126 bp, an allele frequency of 0.15904 (17,585 of 110,570 alleles), and a HIGH_NCR filter status. (kind: database_fact; confidence: high; evidence: GNO-BL-001)
- Eight dbVar records (nsv3552129, nsv3947452, nsv4438715, nsv5167875, nsv5535033, nsv5605727, nsv5948684, nsv6062347) document insertions or mobile element insertions matching coordinate 3:49404094 exactly. (kind: database_fact; confidence: high; evidence: DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008)

## Clinical evidence and phenotype associations

No evidence recorded.

## Literature evidence

No evidence recorded.

## Possible interpretations

- The technical quality and alignment validity of the insertion call cannot be established due to unknown artifact risks regarding call rate, single caller support, repeat region status, low mappability, and genotype quality. (kind: observation; confidence: high; evidence: QC-BL-001, QC-BL-002, QC-BL-003, QC-BL-004, QC-BL-005, QC-BL-006, QC-BL-007)

## Qualified findings

- A mobile element insertion from study nstd203 (nsv5166842) matches the insertion region via a partial region overlap (3:49404092-49404144). (evidence: DBV-BL-009; qualification: dbVar record nsv5166842 spans 3:49404092-49404144 as a mobile element insertion from nstd203, establishing regional overlap.; Cited database records do not establish an exact or high-similarity match.)
- An insertion from study nstd162 (nsv3380534) matches near coordinate 3:49404095. (evidence: DBV-BL-010; qualification: dbVar record nsv3380534 matches at the adjacent 3:49404095 coordinate.; Cited database records do not establish an exact or high-similarity match.)
- General literature on RHOA describes its roles in cell motility, 3D invasive migration, and interactions with other proteins such as Septin11 and phospholipase C̵, but does not reference this specific insertion. (evidence: PMID-34635648, PMID-41359424, PMID-32640259, PMID-41006770, PMID-37080972; qualification: The literature references describe various biological activities of RHOA but do not describe or validate this specific structural variant.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- Literature on the Genome in a Bottle (GIAB) consortium and sequencing methodologies outlines benchmark pipelines and RNA-seq diagnostic validation but does not provide direct evidence for this specific insertion. (evidence: PMID-34965940, PMID-40043707, PMID-31406327, PMID-35789587, PMID-31888441; qualification: The cited PMIDs reference generic benchmark methodologies and pipeline validation papers rather than this specific insertion.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- It is hypothesized that the 663 bp insertion is an intronic mobile element insertion in RHOA, as indicated by the intronic consequence annotation of the highly similar gnomAD candidate INS_chr3_9224a6a5 and the exact coordinate overlap with several RHOA transcript spans. (evidence: GNO-BL-001, ENS-ADP-NOMINAL-TRANSCRIPT-009; qualification: The hypothesis is logically sound and directly supported by the intronic status of the highly similar gnomAD candidate INS_chr3_9224a6a5 and the overlap with the canonical RHOA transcript model.; A hypothesis is not an established finding.)

## Artifact risks

- **low_call_rate — unknown**: Missingness can produce spurious population differences. Recommended check: Calculate call rate per cohort.
- **single_caller_support — unknown**: A call from one algorithm may reflect caller-specific bias. Recommended check: Validate with an orthogonal caller or experimental assay.
- **repeat_region — unknown**: Repeats in breakpoint windows can make breakpoint placement unreliable. Recommended check: Confirm both breakpoints against a curated repeat track.
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
- Similarity metrics for gnomAD-SV and dbVar records do not prove exact molecular or sequence identity to the query insertion.
- Literature search results reflect only general gene-level functions and generic GIAB benchmarks, without specific validation of the investigated RHOA insertion.
- Clinical databases do not contain information regarding this insertion, meaning its clinical relevance remains undetermined.
- Dropped factual candidate claims without evidence IDs: C08
- Baseline Ensembl API queries for genes, regulatory regions, and repeat annotations at the breakpoints failed (HTTP 500), leaving spatial overlap unconfirmed through baseline pipelines.
- There is an absence of direct patient-level clinical annotations, experimental validation of this specific insertion, or any ClinVar submissions.
- All QC artifact risk parameters (such as call rate, repeat status, mappability, and supporting reads) are flagged as unknown.
- Baseline Ensembl region overlap queries failed with HTTP 500. Verification relies on fallback nearest-gene and transcript queries.
- Candidate similarity metrics from gnomAD-SV and dbVar records do not establish exact sequence identity or identical biological events.
- Conservatively qualified claim C06: Cited database records do not establish an exact or high-similarity match.
- Conservatively qualified claim C07: Cited database records do not establish an exact or high-similarity match.
- Conservatively qualified claim C09: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C10: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C11: A hypothesis is not an established finding.
- Ensembl query was incomplete (error).
- Ensembl VEP query was incomplete (error).

## Recommended next steps

- Resolve evidence gap: Baseline Ensembl API queries for genes, regulatory regions, and repeat annotations at the breakpoints failed (HTTP 500), leaving spatial overlap unconfirmed through baseline pipelines.
- Resolve evidence gap: There is an absence of direct patient-level clinical annotations, experimental validation of this specific insertion, or any ClinVar submissions.
- Resolve evidence gap: All QC artifact risk parameters (such as call rate, repeat status, mappability, and supporting reads) are flagged as unknown.

## Evidence catalog

- **DBV-BL-001** [dbVar; exact]: dbVar record nsv3552129 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3552129/
- **DBV-BL-002** [dbVar; exact]: dbVar record nsv3947452 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3947452/
- **DBV-BL-003** [dbVar; exact]: dbVar record nsv4438715 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv4438715/
- **DBV-BL-004** [dbVar; exact]: dbVar record nsv5167875 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5167875/
- **DBV-BL-005** [dbVar; exact]: dbVar record nsv5535033 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5535033/
- **DBV-BL-006** [dbVar; exact]: dbVar record nsv5605727 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5605727/
- **DBV-BL-007** [dbVar; exact]: dbVar record nsv5948684 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5948684/
- **DBV-BL-008** [dbVar; exact]: dbVar record nsv6062347 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6062347/
- **DBV-BL-009** [dbVar; region_overlap]: dbVar record nsv5166842 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5166842/
- **DBV-BL-010** [dbVar; nearby]: dbVar record nsv3380534 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3380534/
- **ENS-ADP-EXPANDED_REGION-GENE-001** [Ensembl; contextual]: novel protein
- **ENS-ADP-EXPANDED_REGION-GENE-002** [Ensembl; contextual]: T cell leukemia translocation altered [Source:HGNC Symbol;Acc:HGNC:11692]
- **ENS-ADP-EXPANDED_REGION-GENE-003** [Ensembl; contextual]: ras homolog family member A [Source:HGNC Symbol;Acc:HGNC:667]
- **ENS-ADP-NOMINAL-TRANSCRIPT-001** [Ensembl; contextual]: Ensembl record ENST00000704381
- **ENS-ADP-NOMINAL-TRANSCRIPT-002** [Ensembl; contextual]: RHOA-203
- **ENS-ADP-NOMINAL-TRANSCRIPT-003** [Ensembl; contextual]: RHOA-209
- **ENS-ADP-NOMINAL-TRANSCRIPT-004** [Ensembl; contextual]: RHOA-206
- **ENS-ADP-NOMINAL-TRANSCRIPT-005** [Ensembl; contextual]: RHOA-205
- **ENS-ADP-NOMINAL-TRANSCRIPT-006** [Ensembl; contextual]: RHOA-210
- **ENS-ADP-NOMINAL-TRANSCRIPT-007** [Ensembl; contextual]: RHOA-207
- **ENS-ADP-NOMINAL-TRANSCRIPT-008** [Ensembl; contextual]: RHOA-211
- **ENS-ADP-NOMINAL-TRANSCRIPT-009** [Ensembl; contextual]: RHOA-202
- **ENS-ADP-NOMINAL-TRANSCRIPT-010** [Ensembl; contextual]: RHOA-208
- **GNO-BL-001** [gnomAD-SV; high_similarity]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/INS_chr3_9224a6a5?dataset=gnomad_sv_r4
- **PMID-31406327** [PubMed; contextual]: Accurate circular consensus long-read sequencing improves variant detection and assembly of a human genome. — https://pubmed.ncbi.nlm.nih.gov/31406327/
- **PMID-31888441** [PubMed; contextual]: VariFAST: a variant filter by automated scoring based on tagged-signatures. — https://pubmed.ncbi.nlm.nih.gov/31888441/
- **PMID-32640259** [PubMed; contextual]: An Oncogenic Alteration Creates a Microenvironment that Promotes Tumor Progression by Conferring a Metabolic Advantage to Regulatory T Cells. — https://pubmed.ncbi.nlm.nih.gov/32640259/
- **PMID-34635648** [PubMed; contextual]: Homeostatic membrane tension constrains cancer cell dissemination by counteracting BAR protein assembly. — https://pubmed.ncbi.nlm.nih.gov/34635648/
- **PMID-34965940** [PubMed; contextual]: Benchmarking small-variant genotyping in polyploids. — https://pubmed.ncbi.nlm.nih.gov/34965940/
- **PMID-35789587** [PubMed; contextual]: Quality control of large genome datasets. — https://pubmed.ncbi.nlm.nih.gov/35789587/
- **PMID-37080972** [PubMed; contextual]: Septin11 promotes hepatocellular carcinoma cell motility by activating RhoA to regulate cytoskeleton and cell adhesion. — https://pubmed.ncbi.nlm.nih.gov/37080972/
- **PMID-40043707** [PubMed; contextual]: Clinical validation of RNA sequencing for Mendelian disorder diagnostics. — https://pubmed.ncbi.nlm.nih.gov/40043707/
- **PMID-41006770** [PubMed; contextual]: RhoA allosterically activates phospholipase Cε via its EF hands. — https://pubmed.ncbi.nlm.nih.gov/41006770/
- **PMID-41359424** [PubMed; contextual]: Context-dependent inhibitory roles of RhoA in 3D invasive cell migration within the extracellular matrix. — https://pubmed.ncbi.nlm.nih.gov/41359424/
- **QC-BL-001** [Artifact-risk rules; contextual]: low_call_rate
- **QC-BL-002** [Artifact-risk rules; contextual]: single_caller_support
- **QC-BL-003** [Artifact-risk rules; contextual]: repeat_region
- **QC-BL-004** [Artifact-risk rules; contextual]: low_mappability
- **QC-BL-005** [Artifact-risk rules; contextual]: supporting_reads
- **QC-BL-006** [Artifact-risk rules; contextual]: genotype_quality
- **QC-BL-007** [Artifact-risk rules; contextual]: batch_effect

## Query provenance

- Ensembl: error — {"query_region": "3:49404094-49404094"}
- Ensembl VEP: error — {}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "3", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: not_applicable — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: not_found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
- PubMed: not_found — (RHOA) AND (GIAB OR "Genome in a Bottle" OR "CMRG")
- PubMed: found — RHOA AND ("Alu" OR "retrotransposon" OR "L1" OR "insertion" OR "SINE" OR "LINE" OR "mobile element")
- PubMed: found — ("Genome in a Bottle" OR "GIAB" OR "CMRG") AND (benchmark OR "medical genes" OR "medically relevant")
