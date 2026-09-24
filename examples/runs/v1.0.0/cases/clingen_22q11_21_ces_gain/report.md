# Structural Variant Investigation Report

**Status:** incomplete

## Variant summary

| Field | Value |
|---|---|
| SV ID | `TEST_GRCh38_22q11.21_CES_region_gain` |
| Reference build | GRCh38 |
| Position | chr22:16912063-18109094 |
| SV type | DUP |
| Coordinate system | 1-based-inclusive |
| Length | 1197032 bp |
| Breakpoint uncertainty | not_provided; start CI=not provided; end CI=not provided |

## Baseline source checks

| Database or resource | Result |
|---|---|
| Ensembl | Found |
| Ensembl VEP | Query failed |
| gnomAD-SV | Found |
| ClinGen Dosage | Found |
| ClinVar | Found |
| NCBI dbVar | Found |
| DGV Gold Standard | Found |

## Adaptive investigation

- Query budget used: 2/2
- Stop reason: The two-call budget is fully exhausted. Both attempted follow-ups targeting Ensembl API endpoints failed with server-side errors (HTTP 500) due to the large scale of the queried genomic interval.
- QUERY_TRANSCRIPTS — executed: VEP failed with a TimeoutError, leading to a complete lack of transcript-specific consequences, annotations, and a truncated gene list for this 1.2 Mb deletion/duplication.
- QUERY_NEAREST_GENE_10KB — executed: Ensembl nominal gene results were truncated and we lack context on whether any high-impact protein-coding genes are located near the breakpoints.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The duplication has an exact coordinate and classification match with ClinGen region curation ISCA-37393, which is assessed as having sufficient evidence for triplosensitivity. (kind: database_fact; confidence: high; evidence: CGD-BL-001)
- The duplication overlaps several regional genes, including GAB4, ADA2, ATP6V1E1, and PEX26, which are individually assessed by ClinGen as having no evidence for triplosensitivity or are not yet evaluated. (kind: database_fact; confidence: high; evidence: CGD-BL-002, CGD-BL-003, CGD-BL-004, CGD-BL-005, CGD-BL-006)
- The duplication has repeat elements present in both the start and end breakpoint windows, as flagged by the quality control check. (kind: observation; confidence: high; evidence: QC-BL-003)

## Population and variant-database evidence

- An exact coordinate duplication match is present in gnomAD-SV (variant ID GD_22q11.21__DUP) with a low allele frequency of 8e-06. (kind: database_fact; confidence: high; evidence: GNO-BL-001)
- Multiple copy-number gain variants are reported in DGV and dbVar that partially overlap the duplication region. (kind: database_fact; confidence: medium; evidence: DGV-BL-001, DGV-BL-002, DGV-BL-003, DGV-BL-004, DGV-BL-005, DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008, DBV-BL-009, DBV-BL-010)

## Clinical evidence and phenotype associations

- ClinVar contains a regional overlapping duplication variant within the ADA2 gene (VCV000583739.4) classified as of uncertain significance. (kind: database_fact; confidence: high; evidence: CLV-BL-001)
- ClinVar contains a regional overlapping duplication variant within the ATP6V1E1 gene (VCV004847812.1) classified as of uncertain significance. (kind: database_fact; confidence: high; evidence: CLV-BL-002)

## Literature evidence

No evidence recorded.

## Possible interpretations

No evidence recorded.

## Qualified findings

- Literature reports from a three-generation family describe a 600 kb triplication in the cat eye syndrome critical region causing anorectal, renal, and preauricular anomalies. (evidence: PMID-22395867; qualification: PMID-22395867 title directly supports this exact clinical and molecular report.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- Literature reports clinical and cytogenetic findings of cat eye syndrome in a 2-year-old patient with congenital aural atresia and hearing loss. (evidence: PMID-39402511; qualification: PMID-39402511 title directly supports this exact case report.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- Literature searches retrieved studies of the human CECR1 gene as a candidate for cat eye syndrome and animal models of Cecr2 as model of human cat eye syndrome. (evidence: PMID-10756095, PMID-33542446; qualification: PMID-10756095 links human CECR1 to cat eye syndrome, and PMID-33542446 describes Cecr2 mutant mice as models.; Only PubMed citation metadata was retrieved; full-text support was not checked.)

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
- The presence of repeat elements at both the start and end breakpoints reduces the confidence in precise coordinate placement and caller consistency.
- Overlapping clinical classifications from ClinVar for regional genes (ADA2, ATP6V1E1) represent candidate variants rather than establishing direct diagnostic causality for the entire 1.2 Mb duplication.
- PMID references are based on literature metadata and search queries, which are contextual and do not prove causal biological mechanisms for this specific structural variant.
- Dropped factual candidate claims without evidence IDs: C010, C011
- Conservatively qualified claim C008: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C009: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C012: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Ensembl VEP query was incomplete (error).

## Recommended next steps

- Resolve evidence gap: Ensembl VEP analysis timed out, leaving predicted consequences and transcript-specific annotations unavailable.
- Resolve evidence gap: Adaptive tools for transcripts and nearest gene within 10kb failed with HTTP 500 errors, creating a gap in precise boundary annotation.
- Resolve evidence gap: No experimental functional data was retrieved directly for this exact genomic duplication.

## Evidence catalog

- **CGD-BL-001** [ClinGen Dosage; exact]: ClinGen Dosage record ISCA-37393 — https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-37393
- **CGD-BL-002** [ClinGen Dosage; region_overlap]: ClinGen Dosage record HGNC:18325 — https://search.clinicalgenome.org/kb/gene-dosage/HGNC:18325
- **CGD-BL-003** [ClinGen Dosage; region_overlap]: ClinGen Dosage record HGNC:1839 — https://search.clinicalgenome.org/kb/gene-dosage/HGNC:1839
- **CGD-BL-004** [ClinGen Dosage; region_overlap]: ClinGen Dosage record HGNC:857 — https://search.clinicalgenome.org/kb/gene-dosage/HGNC:857
- **CGD-BL-005** [ClinGen Dosage; region_overlap]: ClinGen Dosage record HGNC:5985 — https://search.clinicalgenome.org/kb/gene-dosage/HGNC:5985
- **CGD-BL-006** [ClinGen Dosage; region_overlap]: ClinGen Dosage record HGNC:22965 — https://search.clinicalgenome.org/kb/gene-dosage/HGNC:22965
- **CLV-BL-001** [ClinVar; region_overlap]: NC_000022.10:g.(?_17662353)_(17663671_?)dup — https://www.ncbi.nlm.nih.gov/clinvar/variation/583739/
- **CLV-BL-002** [ClinVar; region_overlap]: NM_001696.4(ATP6V1E1):c.100-57_115dup — https://www.ncbi.nlm.nih.gov/clinvar/variation/4847812/
- **DBV-BL-001** [dbVar; region_overlap]: dbVar record nsv7776212 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776212/
- **DBV-BL-002** [dbVar; region_overlap]: dbVar record nsv7776041 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776041/
- **DBV-BL-003** [dbVar; region_overlap]: dbVar record nsv7776770 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776770/
- **DBV-BL-004** [dbVar; region_overlap]: dbVar record nsv7776169 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776169/
- **DBV-BL-005** [dbVar; region_overlap]: dbVar record nsv7908466 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7908466/
- **DBV-BL-006** [dbVar; region_overlap]: dbVar record nsv7776615 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776615/
- **DBV-BL-007** [dbVar; region_overlap]: dbVar record nsv7776399 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776399/
- **DBV-BL-008** [dbVar; region_overlap]: dbVar record nsv7776486 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776486/
- **DBV-BL-009** [dbVar; region_overlap]: dbVar record nsv7776392 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776392/
- **DBV-BL-010** [dbVar; region_overlap]: dbVar record nsv7776462 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7776462/
- **DGV-BL-001** [DGV Gold; region_overlap]: DGV Gold record gssvG23664 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=17069324;end=17142761
- **DGV-BL-002** [DGV Gold; region_overlap]: DGV Gold record gssvG23684 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=17023054;end=17034926
- **DGV-BL-003** [DGV Gold; region_overlap]: DGV Gold record gssvG23735 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=17658014;end=17662058
- **DGV-BL-004** [DGV Gold; region_overlap]: DGV Gold record gssvG23655 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=16367187;end=17135620
- **DGV-BL-005** [DGV Gold; region_overlap]: DGV Gold record gssvG23745 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=18062620;end=19019471
- **GNO-BL-001** [gnomAD-SV; exact]: Exact coordinate and compatible-type match. — https://gnomad.broadinstitute.org/variant/GD_22q11.21__DUP?dataset=gnomad_sv_r4
- **PMID-10756095** [PubMed; contextual]: The human homolog of insect-derived growth factor, CECR1, is a candidate gene for features of cat eye syndrome. — https://pubmed.ncbi.nlm.nih.gov/10756095/
- **PMID-22395867** [PubMed; contextual]: A 600 kb triplication in the cat eye syndrome critical region causes anorectal, renal and preauricular anomalies in a three-generation family. — https://pubmed.ncbi.nlm.nih.gov/22395867/
- **PMID-33542446** [PubMed; contextual]: Cecr2 mutant mice as a model for human cat eye syndrome. — https://pubmed.ncbi.nlm.nih.gov/33542446/
- **PMID-39402511** [PubMed; contextual]: Clinical and molecular cytogenetic findings of cat eye syndrome and a 2-year-old patient with congenital aural atresia and hearing loss. — https://pubmed.ncbi.nlm.nih.gov/39402511/
- **QC-BL-001** [Artifact-risk rules; contextual]: low_call_rate
- **QC-BL-002** [Artifact-risk rules; contextual]: single_caller_support
- **QC-BL-003** [Artifact-risk rules; contextual]: repeat_region
- **QC-BL-004** [Artifact-risk rules; contextual]: low_mappability
- **QC-BL-005** [Artifact-risk rules; contextual]: supporting_reads
- **QC-BL-006** [Artifact-risk rules; contextual]: genotype_quality
- **QC-BL-007** [Artifact-risk rules; contextual]: batch_effect

## Query provenance

- Ensembl: found — {"query_region": "22:16912063-18109094"}
- Ensembl VEP: error — {}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "22", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: found — {}
- ClinVar: found — {"query_regions": [{"role": "nominal", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- PubMed: found — "22:16912063-18109094" OR ("16912063" AND "18109094")
- PubMed: found — (CECR2 OR ADA2 OR ATP6V1E1) AND ("copy number gain" OR "duplication")
- PubMed: found — (ADA2 OR PEX26 OR IL17RA) AND duplication
