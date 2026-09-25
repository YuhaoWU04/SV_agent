# Structural Variant Investigation Report

**Status:** complete

## Variant summary

| Field | Value |
|---|---|
| SV ID | `TEST_GRCh38_22q11.2_distal_type1_region_DEL` |
| Reference build | GRCh38 |
| Position | chr22:21562828-22620608 |
| SV type | DEL |
| Coordinate system | 1-based-inclusive |
| Length | 1057781 bp |
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
- Stop reason: Sufficient evidence exists to characterize the variant based on the provided baseline data.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The SV encompasses multiple protein-coding genes including MAPK1, UBE2L3, TOP3B, and PPIL2, with predicted high-impact transcript ablation consequences. (kind: database_fact; confidence: high; evidence: VEP-BL-001, VEP-BL-008, VEP-BL-009, VEP-BL-010)
- The SV breakpoints contain repeat elements (e.g., ERV3-16A3_I-int, AluSx1) which can make precise breakpoint mapping unreliable. (kind: observation; confidence: high; evidence: ENS-BL-END-REPEAT-001, ENS-BL-END-REPEAT-002, QC-BL-003)

## Population and variant-database evidence

- Population databases (gnomAD-SV, DGV) contain multiple deletion variants that show partial or regional overlap with the SV coordinates. (kind: database_fact; confidence: high; evidence: GNO-BL-001, GNO-BL-003, DGV-BL-001, DGV-BL-002)

## Clinical evidence and phenotype associations

- The SV region overlaps the 22q11.2 recurrent distal type I (D-E or D-F) region, which is curated by ClinGen as having sufficient evidence for haploinsufficiency. (kind: database_fact; confidence: high; evidence: CGD-BL-001)
- ClinVar lists pathogenic and likely pathogenic deletion variants in this 22q11.2 region associated with 22q11.2 deletion syndrome, schizophrenia, and autism. (kind: database_fact; confidence: high; evidence: CLV-BL-001, CLV-BL-002, CLV-BL-003, CLV-BL-004)

## Literature evidence

No evidence recorded.

## Possible interpretations

No evidence recorded.

## Qualified findings

- The presence of partial overlap in population and clinical databases does not establish that the queried SV is identical to any individual submitted clinical or population record. (evidence: CLV-BL-001, GNO-BL-001, DBV-BL-001; qualification: Cited database records do not establish an exact or high-similarity match.)

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
- Conservatively qualified claim C006: Cited database records do not establish an exact or high-similarity match.

## Recommended next steps

- Resolve evidence gap: No experimental validation of dosage sensitivity for the specific genes in this SV.
- Resolve evidence gap: Lack of patient-specific clinical data to correlate phenotype with the variant genotype.
- Resolve evidence gap: Absence of orthogonal caller support data to rule out single-caller bias.

## Evidence catalog

### ClinGen Dosage

- **CGD-BL-001** (Sufficient Evidence for Haploinsufficiency; exact): ClinGen dosage record for 22q11.2 recurrent region (distal type I, D-E or D-F): Sufficient Evidence for Haploinsufficiency.
  - Key facts: entity="22q11.2 recurrent region (distal type I, D-E or D-F)"; entity_type="region"; relevant_dosage_direction="haploinsufficiency"; relevant_assessment="Sufficient Evidence for Haploinsufficiency"; haploinsufficiency={"assessment": "Sufficient Evidence for Haploinsufficiency", "score": 3}; triplosensitivity={"assessment": "Little Evidence for Triplosensitivity", "score": 1}; position="22:21562828-22620608"
  - Used by: clinical_phenotype_evidence[1], verified_claims.C001
  - Source: https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-37397
- **Source limitation:** ClinGen dosage scores are expert-curated gene/region evidence, not a patient-level classification. Coordinate overlap does not establish that recurrent breakpoints, copy state, phenotype, inheritance, or structural configuration match the curated cases.

### ClinVar

- **CLV-BL-001** (Pathogenic; partial_overlap): ClinVar VCV004891287.1: Pathogenic (criteria provided, single submitter).
  - Key facts: variant_type="Deletion"; germline_classification="Pathogenic"; review_status="criteria provided, single submitter"; traits=["Chromosome 22q11.2 deletion syndrome, distal"]; genes=["CCDC116", "IGL", "IGLV1-36", "IGLV1-40", "IGLV1-44", "IGLV1-47", "IGLV1-50", "IGLV1-51", "IGLV10-54", "IGLV11-55"]; supporting_scv_count=1; match_metrics={"start_offset_bp": 868, "end_offset_bp": 1052, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.999179, "reciprocal_overlap_database": 0.999006, "size_similarity": 0.999826}; position="22:21563696-22621660"
  - Used by: clinical_phenotype_evidence[2], verified_claims.C002, verified_claims.C006
  - Source: https://www.ncbi.nlm.nih.gov/clinvar/variation/4891287/
- **CLV-BL-002** (Likely pathogenic; region_overlap): ClinVar VCV000545270.1: Likely pathogenic (criteria provided, single submitter).
  - Key facts: variant_type="Deletion"; germline_classification="Likely pathogenic"; review_status="criteria provided, single submitter"; traits=["Schizophrenia"]; genes=["IGL", "IGLV10-54", "IGLV11-55", "IGLV4-60", "IGLV4-69", "IGLV6-57", "IGLV8-61", "LOC112694768", "LOC125424390", "LOC130067043"]; supporting_scv_count=1; match_metrics={"start_offset_bp": 393179, "end_offset_bp": -396420, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.253533, "reciprocal_overlap_database": 1.0, "size_similarity": 0.253533}; position="22:21956007-22224188"
  - Used by: clinical_phenotype_evidence[2], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/clinvar/variation/545270/
- **CLV-BL-003** (Likely pathogenic; region_overlap): ClinVar VCV000545271.1: Likely pathogenic (criteria provided, single submitter).
  - Key facts: variant_type="Deletion"; germline_classification="Likely pathogenic"; review_status="criteria provided, single submitter"; traits=["Autism"]; genes=["IGL", "IGLV10-54", "IGLV11-55", "IGLV4-60", "IGLV4-69", "IGLV6-57", "IGLV8-61", "LOC112694768", "LOC125424390", "LOC130067043"]; supporting_scv_count=1; match_metrics={"start_offset_bp": 396401, "end_offset_bp": -402088, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.245128, "reciprocal_overlap_database": 1.0, "size_similarity": 0.245128}; position="22:21959229-22218520"
  - Used by: clinical_phenotype_evidence[2], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/clinvar/variation/545271/
- **CLV-BL-004** (Pathogenic; region_overlap): ClinVar VCV004974535.1: Pathogenic (criteria provided, single submitter).
  - Key facts: variant_type="Deletion"; germline_classification="Pathogenic"; review_status="criteria provided, single submitter"; traits=["DiGeorge syndrome"]; genes=["FAM230B", "LOC132090632", "FAM230F", "LOC132090633", "LRRC74B", "LRRC74BNL", "LOC132090635", "GNB1L", "KLHL22", "LINC00895"]; supporting_scv_count=1; match_metrics={"start_offset_bp": -2688019, "end_offset_bp": -1049652, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.007685, "reciprocal_overlap_database": 0.003015, "size_similarity": 0.39233}; position="22:18874809-21570956"
  - Used by: clinical_phenotype_evidence[2], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/clinvar/variation/4974535/
- **Source limitation:** ClinVar contains submitted aggregate interpretations with different review levels and possible conflicts. Exact displayed coordinates and compatible type do not establish the same biological event. Inner/outer bounds, condition, review status, and last evaluation must be considered; absence from this bounded search does not establish novelty or benignity.

### dbVar

- **DBV-BL-001** (ambiguous_cnv_direction; partial_overlap): dbVar nsv7907941: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd102"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; clinical_significance=["Uncertain significance"]; genes=[{"id": 266700, "name": "BMP6P1"}, {"id": 28773, "name": "IGLV9-49"}, {"id": 28787, "name": "IGLV3-32"}, {"id": 129025, "name": "ZNF280A"}, {"id": 100419915, "name": "LOC100419915"}, {"id": 28790, "name": "IGLV3-29"}, {"id": 28770, "name": "IGLV11-55"}, {"id": 28759, "name": "IGLVIV-65"}, {"id": 3535, "name": "IGL"}, {"id": 28779, "name": "IGLV5-52"}]; methods=["Multiple"]; match_metrics={"start_offset_bp": -2021, "end_offset_bp": 259076, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.802031, "size_similarity": 0.802031}; position="22:21560807-22879684"
  - Used by: verified_claims.C006
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7907941/
- **Source limitation:** dbVar aggregates submitter-defined variant regions and calls from many studies and technologies. Boundaries may be imprecise or remapped, a generic copy-number type may not establish DEL versus DUP direction, and this bounded endpoint search does not retrieve every enclosing record. A match is contextual evidence, not proof of event identity, clinical significance, or validation.

### DGV Gold

- **DGV-BL-001** (partial_overlap): DGV Gold gssvL76611: partial_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Loss"; frequency="0.553203%"; num_unique_samples_tested=14642; num_samples_with_variant=81; num_studies=4; match_metrics={"start_offset_bp": 397877, "end_offset_bp": 295591, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.623857, "reciprocal_overlap_database": 0.690641, "size_similarity": 0.903301}; position="22:21960705-22916199"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=21960704;end=22916199
- **DGV-BL-002** (region_overlap): DGV Gold gssvL76614: region_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Loss"; frequency="0.290006%"; num_unique_samples_tested=17241; num_samples_with_variant=50; num_studies=5; match_metrics={"start_offset_bp": 380447, "end_offset_bp": -374738, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.286067, "reciprocal_overlap_database": 1.0, "size_similarity": 0.286067}; position="22:21943275-22245870"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=21943274;end=22245870
- **Source limitation:** This adapter queries the curated DGV Gold Standard track exposed by UCSC, not the complete current DGV release. DGV aggregates healthy-control studies with heterogeneous platforms and often imprecise boundaries. Overlap or frequency is contextual population evidence, not proof of the same event, benignity, or absence of clinical effect.

### Ensembl

- **ENS-BL-END-REPEAT-001** (breakpoint_window_hit; region_overlap): repeat ENS-BL-END-REPEAT-001 found in the end region.
  - Key facts: feature_type="repeat"; breakpoint_role="end"; position="22:22620108-22620375"
  - Used by: gene_region_annotation[2], verified_claims.C005
- **ENS-BL-END-REPEAT-002** (breakpoint_window_hit; region_overlap): repeat ENS-BL-END-REPEAT-002 found in the end region.
  - Key facts: feature_type="repeat"; breakpoint_role="end"; position="22:22620610-22620782"
  - Used by: gene_region_annotation[2], verified_claims.C005
- **Source limitation:** Spatial overlap only: sv_type is retained for provenance but does not change this query. Nominal-interval and breakpoint-window results are reported separately; a parsed BND mate is also queried separately. Each scope first combines gene, regulatory, and repeat features; a failed combined request falls back to serialized per-feature queries. A heuristic breakpoint window retrieves nearby features but is not a measured confidence interval. Results are capped per feature type; transcript, consequence, breakpoint, nearest-gene, and mappability annotation are not included. A null feature list means that feature query failed.

### gnomAD-SV

- **GNO-BL-001** (partial_overlap): gnomAD-SV DEL_chr22_393105dd is a partial_overlap match (AF=8e-06).
  - Key facts: variant_id="DEL_chr22_393105dd"; type="DEL"; af=8e-06; ac=1; an=126028; filters=["IGH_MHC_OVERLAP"]; match_metrics={"start_offset_bp": 463722, "end_offset_bp": 279012, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.561609, "reciprocal_overlap_database": 0.680425, "size_similarity": 0.82538}; position="22:22026550-22899620"
  - Used by: population_evidence[1], verified_claims.C004, verified_claims.C006
  - Source: https://gnomad.broadinstitute.org/variant/DEL_chr22_393105dd?dataset=gnomad_sv_r4
- **GNO-BL-003** (partial_overlap): gnomAD-SV DEL_chr22_503eb8a7 is a partial_overlap match (AF=5.6e-05).
  - Key facts: variant_id="DEL_chr22_503eb8a7"; type="DEL"; af=5.6e-05; ac=7; an=126050; filters=["IGH_MHC_OVERLAP"]; match_metrics={"start_offset_bp": 463722, "end_offset_bp": 284381, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.561609, "reciprocal_overlap_database": 0.676266, "size_similarity": 0.830455}; position="22:22026550-22904989"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://gnomad.broadinstitute.org/variant/DEL_chr22_503eb8a7?dataset=gnomad_sv_r4
- **Source limitation:** Similarity classes are deterministic screening labels, not proof of variant identity or biological effect. Heuristic windows are used only when VCF breakpoint confidence intervals are unavailable. BND records with a parsed mate are compared using both breakends and the chromosome pair, allowing reversed record order. Input orientation is retained but cannot be compared because it is absent from this gnomAD response. BND records without a mate retain first-breakend-only candidate matching. Adaptive retrieval padding, when nonzero, widens only the records retrieved from the API; it never widens the fixed matching windows. A gnomAD-SV absence does not establish novelty, pathogenicity, or technical validity.

### Artifact-risk rules

- **QC-BL-001** (unknown): low_call_rate: unknown. Missingness can produce spurious population differences.
  - Key facts: risk_type="low_call_rate"; recommended_check="Calculate call rate per cohort."
  - Used by: artifact_risks.low_call_rate
- **QC-BL-002** (unknown): single_caller_support: unknown. A call from one algorithm may reflect caller-specific bias.
  - Key facts: risk_type="single_caller_support"; recommended_check="Validate with an orthogonal caller or experimental assay."
  - Used by: artifact_risks.single_caller_support
- **QC-BL-003** (present): repeat_region: present. Repeats in breakpoint windows can make breakpoint placement unreliable.
  - Key facts: risk_type="repeat_region"; evidence={"scope": "breakpoint_windows", "start_repeat_count": 10, "end_repeat_count": 9}; recommended_check="Confirm both breakpoints against a curated repeat track."
  - Used by: gene_region_annotation[2], artifact_risks.repeat_region, verified_claims.C005
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

- **VEP-BL-001** (high): VEP predicts transcript_ablation for MAPK1 (HIGH).
  - Key facts: gene_symbol="MAPK1"; gene_id="ENSG00000100030"; transcript_id="ENST00000215832"; consequence_terms=["transcript_ablation"]; impact="HIGH"; percentage_overlap=100; canonical=true; mane_select="NM_002745.5"
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-008** (high): VEP predicts transcript_ablation for UBE2L3 (HIGH).
  - Key facts: gene_symbol="UBE2L3"; gene_id="ENSG00000185651"; transcript_id="ENST00000342192"; consequence_terms=["transcript_ablation"]; impact="HIGH"; percentage_overlap=100; canonical=true; mane_select="NM_003347.4"
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-009** (high): VEP predicts transcript_ablation for TOP3B (HIGH).
  - Key facts: gene_symbol="TOP3B"; gene_id="ENSG00000100038"; transcript_id="ENST00000357179"; consequence_terms=["transcript_ablation"]; impact="HIGH"; percentage_overlap=100; canonical=true; mane_select="NM_001282112.2"
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-010** (high): VEP predicts transcript_ablation for PPIL2 (HIGH).
  - Key facts: gene_symbol="PPIL2"; gene_id="ENSG00000100023"; transcript_id="ENST00000398831"; consequence_terms=["transcript_ablation"]; impact="HIGH"; percentage_overlap=100; canonical=true; mane_select="NM_014337.4"
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **Source limitation:** VEP consequences are predictions for the submitted interval and symbolic allele. They do not establish expression change, dosage pathogenicity, phenotype, penetrance, or the actual transcript expressed in a sample. Only a ranked compact subset of consequences is retained.


## Query provenance

- Ensembl: found — {"query_region": "22:21562828-22620608", "query_strategy": "combined"}
- Ensembl VEP: found — {"query_region": "22:21562828-22620608"}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "22", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: found — {}
- ClinVar: found — {"query_regions": [{"role": "nominal", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
