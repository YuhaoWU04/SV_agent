# Structural Variant Investigation Report

**Status:** complete

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
| Ensembl VEP | Found |
| gnomAD-SV | Found |
| ClinGen Dosage | Found |
| ClinVar | Found |
| NCBI dbVar | Found |
| DGV Gold Standard | Found |

## Adaptive investigation

- Query budget used: 0/2
- Stop reason: The candidate region is a well-characterized 22q11.21 recurrent (CES) duplication. Baseline evidence already provides comprehensive gene annotation, clinical dosage sensitivity (triplosensitivity), and extensive population frequency overlap. No further queries are needed to characterize the biological content of this well-known region.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The SV overlaps with multiple genes including ADA2, ATP6V1E1, and IL17RA, which are classified in ClinGen as having either no evidence for triplosensitivity or are not yet evaluated. (kind: database_fact; confidence: high; evidence: CGD-BL-003, CGD-BL-004, CGD-BL-005)
- VEP analysis predicts high-impact consequences (transcript_amplification) for genes including ATP6V1E1, CECR2, and ADA2. (kind: database_fact; confidence: high; evidence: VEP-BL-001, VEP-BL-002, VEP-BL-009)

## Population and variant-database evidence

- The duplication is identified in gnomAD-SV at the exact reported coordinates. (kind: observation; confidence: high; evidence: GNO-BL-001)

## Clinical evidence and phenotype associations

- The SV corresponds to the 22q11.21 recurrent (CES) region, which is documented in the ClinGen dosage database as having sufficient evidence for triplosensitivity. (kind: database_fact; confidence: high; evidence: CGD-BL-001)

## Literature evidence

No evidence recorded.

## Possible interpretations

- Breakpoint regions contain repetitive sequences, which may affect the reliability of breakpoint placement. (kind: inference; confidence: high; evidence: QC-BL-003)

## Qualified findings

- Literature exists reporting copy number variants in 22q11.21 in patients with diverse phenotypes including infertility, esophageal atresia, and autism spectrum disorders. (evidence: PMID-41338233, PMID-26625662, PMID-42653435; qualification: Only PubMed citation metadata was retrieved; full-text support was not checked.)

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
- Baseline Ensembl evidence is coordinate-overlap evidence only.
- VEP consequences are bioinformatic predictions for a symbolic allele and do not constitute experimental validation or evidence of clinical consequence.
- ClinGen dosage scores are expert-curated regional assessments, not diagnostic classifications for a specific patient's variant.
- gnomAD and DGV frequency data serve as population context and do not establish the pathogenicity or benignity of the variant.
- PubMed metadata summarizes study topics but does not equate to the verification of specific biological claims or clinical diagnoses.
- ClinGen gene-level evidence refers to dosage sensitivity of genes, whereas the regional assessment (C001) pertains to the 22q11.21 recurrent region; ensure the distinction between gene-level and region-level curation is maintained in final reporting.
- Conservatively qualified claim C005: Only PubMed citation metadata was retrieved; full-text support was not checked.

## Recommended next steps

- Resolve evidence gap: No direct patient-level clinical report was retrieved confirming the pathogenicity of this specific duplication in a diagnostic context.
- Resolve evidence gap: The literature search did not yield specific documentation linking the queried region to 'CATSLIP' or specific CAT eye syndrome triplosensitivity mechanisms.

## Evidence catalog

### ClinGen Dosage

- **CGD-BL-001** (Sufficient Evidence for Triplosensitivity; exact): ClinGen dosage record for 22q11.21 recurrent (CES) region (includes CECR2): Sufficient Evidence for Triplosensitivity.
  - Key facts: entity="22q11.21 recurrent (CES) region (includes CECR2)"; entity_type="region"; relevant_dosage_direction="triplosensitivity"; relevant_assessment="Sufficient Evidence for Triplosensitivity"; haploinsufficiency={"assessment": "Little Evidence for Haploinsufficiency", "score": 1}; triplosensitivity={"assessment": "Sufficient Evidence for Triplosensitivity", "score": 3}; position="22:16912063-18109094"
  - Used by: clinical_phenotype_evidence[1], verified_claims.C001
  - Source: https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-37393
- **CGD-BL-003** (No Evidence for Triplosensitivity; region_overlap): ClinGen dosage record for ADA2: No Evidence for Triplosensitivity.
  - Key facts: entity="ADA2"; entity_type="gene"; relevant_dosage_direction="triplosensitivity"; relevant_assessment="No Evidence for Triplosensitivity"; haploinsufficiency={"assessment": "Gene Associated with Autosomal Recessive Phenotype", "score": 30}; triplosensitivity={"assessment": "No Evidence for Triplosensitivity", "score": 0}; position="22:17178790-17221848"
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://search.clinicalgenome.org/kb/gene-dosage/HGNC:1839
- **CGD-BL-004** (No Evidence for Triplosensitivity; region_overlap): ClinGen dosage record for ATP6V1E1: No Evidence for Triplosensitivity.
  - Key facts: entity="ATP6V1E1"; entity_type="gene"; relevant_dosage_direction="triplosensitivity"; relevant_assessment="No Evidence for Triplosensitivity"; haploinsufficiency={"assessment": "No Evidence for Haploinsufficiency", "score": 0}; triplosensitivity={"assessment": "No Evidence for Triplosensitivity", "score": 0}; position="22:17592136-17628822"
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://search.clinicalgenome.org/kb/gene-dosage/HGNC:857
- **CGD-BL-005** (Not yet evaluated; region_overlap): ClinGen dosage record for IL17RA: Not yet evaluated.
  - Key facts: entity="IL17RA"; entity_type="gene"; relevant_dosage_direction="triplosensitivity"; relevant_assessment="Not yet evaluated"; haploinsufficiency={"assessment": "Gene Associated with Autosomal Recessive Phenotype", "score": 30}; triplosensitivity={"assessment": "Not yet evaluated", "score": null}; position="22:17085000-17115693"
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://search.clinicalgenome.org/kb/gene-dosage/HGNC:5985
- **Source limitation:** ClinGen dosage scores are expert-curated gene/region evidence, not a patient-level classification. Coordinate overlap does not establish that recurrent breakpoints, copy state, phenotype, inheritance, or structural configuration match the curated cases.

### gnomAD-SV

- **GNO-BL-001** (exact): gnomAD-SV GD_22q11.21__DUP is a exact match (AF=8e-06).
  - Key facts: variant_id="GD_22q11.21__DUP"; type="DUP"; af=8e-06; ac=1; an=124722; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="22:16912063-18109094"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://gnomad.broadinstitute.org/variant/GD_22q11.21__DUP?dataset=gnomad_sv_r4
- **Source limitation:** Similarity classes are deterministic screening labels, not proof of variant identity or biological effect. Heuristic windows are used only when VCF breakpoint confidence intervals are unavailable. BND records with a parsed mate are compared using both breakends and the chromosome pair, allowing reversed record order. Input orientation is retained but cannot be compared because it is absent from this gnomAD response. BND records without a mate retain first-breakend-only candidate matching. Adaptive retrieval padding, when nonzero, widens only the records retrieved from the API; it never widens the fixed matching windows. A gnomAD-SV absence does not establish novelty, pathogenicity, or technical validity.

### PubMed

- **PMID-26625662** (citation_found): ESOPHAGEAL ATRESIA WITH RECURRENT TRACHEOESOPHAGEAL FISTULAS AND MICRODUPLICATION 22q11.23.
  - Key facts: authors=["Puvabanditsin S", "Garrow E", "February M"]; author_count=5; source="Genet Couns"; pubdate="2015"
  - Used by: verified_claims.C005
  - Source: https://pubmed.ncbi.nlm.nih.gov/26625662/
- **PMID-41338233** (citation_found): Microdeletion and microduplication syndromes, including recurrent rearrangements at 16p11.2 and 22q11.21, are enriched in unexplained male infertility.
  - Key facts: authors=["Kikas T", "Dutta A", "Inno R"]; author_count=9; source="Hum Reprod"; pubdate="2026 Feb 1"; doi="10.1093/humrep/deaf231"
  - Used by: verified_claims.C005
  - Source: https://pubmed.ncbi.nlm.nih.gov/41338233/
- **PMID-42653435** (citation_found): Contribution of Copy Number Variants and Cumulative Genetic Load to Autism Spectrum Disorders: Integrative Insights from Chromosomal Microarray Analysis.
  - Key facts: authors=["Di Iorio MR", "La Monica I", "Imperatore A"]; author_count=7; source="Int J Mol Sci"; pubdate="2026 Aug 20"; doi="10.3390/ijms27167434"
  - Used by: verified_claims.C005
  - Source: https://pubmed.ncbi.nlm.nih.gov/42653435/
- **Source limitation:** Metadata does not prove that the full text supports a biological claim.

### Artifact-risk rules

- **QC-BL-001** (unknown): low_call_rate: unknown. Missingness can produce spurious population differences.
  - Key facts: risk_type="low_call_rate"; recommended_check="Calculate call rate per cohort."
  - Used by: artifact_risks.low_call_rate
- **QC-BL-002** (unknown): single_caller_support: unknown. A call from one algorithm may reflect caller-specific bias.
  - Key facts: risk_type="single_caller_support"; recommended_check="Validate with an orthogonal caller or experimental assay."
  - Used by: artifact_risks.single_caller_support
- **QC-BL-003** (present): repeat_region: present. Repeats in breakpoint windows can make breakpoint placement unreliable.
  - Key facts: risk_type="repeat_region"; evidence={"scope": "breakpoint_windows", "start_repeat_count": 10, "end_repeat_count": 10}; recommended_check="Confirm both breakpoints against a curated repeat track."
  - Used by: artifact_risks.repeat_region, possible_interpretations[1], verified_claims.C006
- **QC-BL-004** (unknown): low_mappability: unknown. Low-mappability sequence can create ambiguous alignments.
  - Key facts: risk_type="low_mappability"; recommended_check="Intersect both breakpoints with a build-matched mappability track."
  - Used by: artifact_risks.low_mappability
- **QC-BL-005** (unknown): supporting_reads: unknown. Weak read support increases false-positive risk.
  - Key facts: risk_type="supporting_reads"; recommended_check="Review caller-specific split-read, paired-end, and depth thresholds."
  - Used by: artifact_risks.supporting_reads
- **QC-BL-006** (unknown): genotype_quality: unknown. Low or missing genotype quality weakens frequency estimates.
  - Key facts: risk_type="genotype_quality"; recommended_check="Inspect genotype likelihoods and quality distributions by cohort."
  - Used by: artifact_risks.genotype_quality
- **QC-BL-007** (unknown): batch_effect: unknown. Unequal pipelines or batches can mimic population differentiation.
  - Key facts: risk_type="batch_effect"; recommended_check="Compare sequencing, coverage, and calling batches between cohorts."
  - Used by: artifact_risks.batch_effect

### Ensembl VEP

- **VEP-BL-001** (high): VEP predicts transcript_amplification for ATP6V1E1 (HIGH).
  - Key facts: gene_symbol="ATP6V1E1"; gene_id="ENSG00000131100"; transcript_id="ENST00000253413"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true; mane_select="NM_001696.4"
  - Used by: gene_region_annotation[2], verified_claims.C004
  - Source: https://rest.ensembl.org/vep/human/region/22:16912063-18109094:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-002** (high): VEP predicts transcript_amplification for CECR2 (HIGH).
  - Key facts: gene_symbol="CECR2"; gene_id="ENSG00000099954"; transcript_id="ENST00000262608"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true; mane_select="NM_001290047.2"
  - Used by: gene_region_annotation[2], verified_claims.C004
  - Source: https://rest.ensembl.org/vep/human/region/22:16912063-18109094:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-009** (high): VEP predicts transcript_amplification for ADA2 (HIGH).
  - Key facts: gene_symbol="ADA2"; gene_id="ENSG00000093072"; transcript_id="ENST00000399837"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true; mane_select="NM_001282225.2"
  - Used by: gene_region_annotation[2], verified_claims.C004
  - Source: https://rest.ensembl.org/vep/human/region/22:16912063-18109094:1/DUP?canonical=1;mane=1;numbers=1
- **Source limitation:** VEP consequences are predictions for the submitted interval and symbolic allele. They do not establish expression change, dosage pathogenicity, phenotype, penetrance, or the actual transcript expressed in a sample. Only a ranked compact subset of consequences is retained.


## Query provenance

- Ensembl: found — {"query_region": "22:16912063-18109094", "query_strategy": "individual_fallback"}
- Ensembl VEP: found — {"query_region": "22:16912063-18109094"}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "22", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: found — {}
- ClinVar: found — {"query_regions": [{"role": "nominal", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [16911563, 18109594]}], "query_strategy": "expanded_full_interval"}
- PubMed: not_found — 22q11.21 duplication triplosensitivity CATSLIP
- PubMed: found — 22q11.21 recurrent duplication clinical phenotype
- PubMed: not_found — 22q11.21 duplication triplosensitivity CAT eye syndrome
