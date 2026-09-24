# Structural Variant Investigation Report

**Status:** complete

## Variant summary

| Field | Value |
|---|---|
| SV ID | `GIAB_CMRG_GRCh38_chr4_1092989_DEL50` |
| Reference build | GRCh38 |
| Position | chr4:1092990-1093039 |
| SV type | DEL |
| Coordinate system | 1-based-inclusive |
| Length | 50 bp |
| Breakpoint uncertainty | not_provided; start CI=not provided; end CI=not provided |

## Baseline source checks

| Database or resource | Result |
|---|---|
| Ensembl | Found |
| Ensembl VEP | Found |
| gnomAD-SV | Found |
| ClinGen Dosage | No record found |
| ClinVar | No record found |
| NCBI dbVar | Found |
| DGV Gold Standard | Found |

## Adaptive investigation

- Query budget used: 0/2
- Stop reason: The candidate is a highly frequent (~58% allele frequency in gnomAD-SV) 50 bp deletion within an intron of RNF212. Whitelisted follow-up actions (such as querying transcripts, exons, or expanding gnomAD retrieval) would not change the interpretation of this common, likely benign population variant.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The 50 bp deletion overlaps the protein-coding gene RNF212 (ENSG00000178222) spanning coordinates 1,056,247 to 1,113,697 on chromosome 4. (kind: database_fact; confidence: high; evidence: ENS-BL-NOMINAL-GENE-001, ENS-BL-START-GENE-001, ENS-BL-END-GENE-001)
- Ensembl VEP predicts that the 50 bp deletion acts as an intron variant (intron 3/9) with MODIFIER impact on the canonical RNF212 transcript ENST00000433731. (kind: database_fact; confidence: high; evidence: VEP-BL-001)
- Ensembl VEP predicts the deletion acts as an intron variant across multiple alternative RNF212 transcripts, including nonsense-mediated decay and retained-intron biotypes. (kind: database_fact; confidence: high; evidence: VEP-BL-002, VEP-BL-003, VEP-BL-004, VEP-BL-005, VEP-BL-006, VEP-BL-007, VEP-BL-008, VEP-BL-009, VEP-BL-010)
- The breakpoint windows of the 50 bp deletion contain Charlie1a repeat elements on both the start and end sides. (kind: observation; confidence: high; evidence: ENS-BL-START-REPEAT-001, ENS-BL-START-REPEAT-002, ENS-BL-END-REPEAT-001, ENS-BL-END-REPEAT-002, QC-BL-003)
- An active regulatory enhancer ENSR4_8TF7 is located near the deletion coordinates at 1,092,388–1,092,550 on chromosome 4 but does not directly overlap the variant. (kind: database_fact; confidence: high; evidence: ENS-BL-START-REGULATORY-001, ENS-BL-END-REGULATORY-001)

## Population and variant-database evidence

- A partially overlapping candidate deletion (variant ID DEL_chr4_09a860e6) has a reported allele frequency of approximately 57.76% (72,835 alleles observed) in the gnomAD-SV database. (kind: database_fact; confidence: high; evidence: GNO-BL-001)
- A partially overlapping copy number loss candidate (variant ID gssvL87089) has a reported frequency of 0.462963% (4 out of 864 samples) across multiple studies in the Database of Genomic Variants (DGV) Gold Standard. (kind: database_fact; confidence: high; evidence: DGV-BL-001)
- Multiple identical and partially overlapping structural variant calls, including esv3833873 with 1,914 variant calls, are documented in dbVar. (kind: database_fact; confidence: high; evidence: DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008, DBV-BL-009, DBV-BL-010)

## Clinical evidence and phenotype associations

No evidence recorded.

## Literature evidence

No evidence recorded.

## Possible interpretations

- Because the deletion is localized entirely within an intron of RNF212 and does not overlap the nearby enhancer ENSR4_8TF7, the transcriptional regulation mediated by this enhancer is inferred to remain unaffected. (kind: inference; confidence: medium; evidence: ENS-BL-START-REGULATORY-001, ENS-BL-END-REGULATORY-001, VEP-BL-001)

## Qualified findings

- PubMed search retrieved a study discussing the role of Foxj3 in mouse spermatogenesis (PMID: 27739607), which does not evaluate or mention this specific 50 bp human RNF212 deletion. (evidence: PMID-27739607; qualification: The publication title and metadata confirm it relates to Foxj3 in mice rather than the human RNF212 deletion.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- Based on the high allele frequency in population databases (57.76% in gnomAD-SV) and VEP-predicted modifier impact, the 50 bp deletion is hypothesized to be a benign polymorphism with no adverse clinical phenotype. (evidence: GNO-BL-001, VEP-BL-001; qualification: Valid scientific hypothesis grounded in high population frequency and non-coding, modifier impact predictions.; A hypothesis is not an established finding.)

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
- Coordinate overlaps in public databases like dbVar and DGV are based on different mapping pipelines and do not establish identical breakpoints or biological events.
- VEP consequence terms are automated predictive models based on transcript models and do not guarantee expression levels or splicing effects in vivo.
- PubMed searches are restricted to abstracts and indexing metadata, potentially omitting full-text mentions or supplementary details regarding this variant.
- Conservatively qualified claim C009: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C011: A hypothesis is not an established finding.

## Recommended next steps

- Resolve evidence gap: No patient-level clinical classifications or phenotypic annotations are available in ClinVar or ClinGen Dosage databases for this specific structural variant.
- Resolve evidence gap: There is an absence of functional or experimental validation in published literature assessing the expression of RNF212 in carriers of this 50 bp intronic deletion.

## Evidence catalog

- **DBV-BL-001** [dbVar; exact]: dbVar record esv3833873 — https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3833873/
- **DBV-BL-002** [dbVar; exact]: dbVar record nsv2809287 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv2809287/
- **DBV-BL-003** [dbVar; exact]: dbVar record nsv3392756 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3392756/
- **DBV-BL-004** [dbVar; exact]: dbVar record nsv4390961 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv4390961/
- **DBV-BL-005** [dbVar; exact]: dbVar record nsv4651823 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv4651823/
- **DBV-BL-006** [dbVar; partial_overlap]: dbVar record dsv2402 — https://www.ncbi.nlm.nih.gov/dbvar/variants/dsv2402/
- **DBV-BL-007** [dbVar; partial_overlap]: dbVar record esv1191684 — https://www.ncbi.nlm.nih.gov/dbvar/variants/esv1191684/
- **DBV-BL-008** [dbVar; partial_overlap]: dbVar record esv3046033 — https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3046033/
- **DBV-BL-009** [dbVar; partial_overlap]: dbVar record esv3494989 — https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3494989/
- **DBV-BL-010** [dbVar; partial_overlap]: dbVar record esv3563229 — https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3563229/
- **DGV-BL-001** [DGV Gold; partial_overlap]: DGV Gold record gssvL87089 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr4;start=1092988;end=1093058
- **ENS-BL-END-GENE-001** [Ensembl; region_overlap]: ring finger protein 212 [Source:HGNC Symbol;Acc:HGNC:27729]
- **ENS-BL-END-REGULATORY-001** [Ensembl; region_overlap]: enhancer
- **ENS-BL-END-REPEAT-001** [Ensembl; region_overlap]: Charlie1a
- **ENS-BL-END-REPEAT-002** [Ensembl; region_overlap]: Charlie1a
- **ENS-BL-NOMINAL-GENE-001** [Ensembl; region_overlap]: ring finger protein 212 [Source:HGNC Symbol;Acc:HGNC:27729]
- **ENS-BL-START-GENE-001** [Ensembl; region_overlap]: ring finger protein 212 [Source:HGNC Symbol;Acc:HGNC:27729]
- **ENS-BL-START-REGULATORY-001** [Ensembl; region_overlap]: enhancer
- **ENS-BL-START-REPEAT-001** [Ensembl; region_overlap]: Charlie1a
- **ENS-BL-START-REPEAT-002** [Ensembl; region_overlap]: Charlie1a
- **GNO-BL-001** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr4_09a860e6?dataset=gnomad_sv_r4
- **PMID-27739607** [PubMed; contextual]: Multiple roles of FOXJ3 in spermatogenesis: A lesson from Foxj3 conditional knockout mouse models. — https://pubmed.ncbi.nlm.nih.gov/27739607/
- **QC-BL-001** [Artifact-risk rules; contextual]: low_call_rate
- **QC-BL-002** [Artifact-risk rules; contextual]: single_caller_support
- **QC-BL-003** [Artifact-risk rules; contextual]: repeat_region
- **QC-BL-004** [Artifact-risk rules; contextual]: low_mappability
- **QC-BL-005** [Artifact-risk rules; contextual]: supporting_reads
- **QC-BL-006** [Artifact-risk rules; contextual]: genotype_quality
- **QC-BL-007** [Artifact-risk rules; contextual]: batch_effect
- **VEP-BL-001** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-002** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-003** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-004** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-005** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-006** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-007** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-008** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-009** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-010** [Ensembl VEP; contextual]: RNF212 — https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1

## Query provenance

- Ensembl: found — {"query_region": "4:1092990-1093039"}
- Ensembl VEP: found — {"query_region": "4:1092990-1093039"}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "4", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: not_found — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- PubMed: found — RNF212 AND (deletion OR "copy number")
- PubMed: not_found — RNF212 AND ("structural variant" OR "structural variation" OR "intronic deletion" OR "intron deletion")
- PubMed: not_found — "esv3833873" OR "nsv2809287" OR "gssvL87089"
