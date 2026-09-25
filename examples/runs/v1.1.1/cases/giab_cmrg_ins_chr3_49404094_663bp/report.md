# Structural Variant Investigation Report

**Status:** complete

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
| Ensembl | Found |
| Ensembl VEP | Found |
| gnomAD-SV | Found |
| ClinGen Dosage | Not applicable |
| ClinVar | No record found |
| NCBI dbVar | Found |
| DGV Gold Standard | No record found |

## Adaptive investigation

- Query budget used: 0/2
- Stop reason: The variant is situated in an intronic region of the RHOA gene, and baseline data already includes gnomAD-SV population frequencies and dbVar records confirming similar insertion events at this locus. Further gene or transcript queries would not materially change the interpretation of this intronic, potentially common insertion.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The variant is located within the gene RHOA (ENSG00000067560). (kind: database_fact; confidence: high; evidence: ENS-BL-NOMINAL-GENE-002)
- The variant is predicted to have an intronic consequence on multiple transcripts of RHOA. (kind: database_fact; confidence: high; evidence: VEP-BL-001, VEP-BL-002, VEP-BL-003, VEP-BL-004, VEP-BL-005, VEP-BL-006, VEP-BL-007, VEP-BL-008, VEP-BL-009, VEP-BL-010)
- The variant overlaps with multiple annotated repeat elements, including AluJo. (kind: database_fact; confidence: high; evidence: ENS-BL-NOMINAL-REPEAT-001, ENS-BL-NOMINAL-REPEAT-002)

## Population and variant-database evidence

- The variant is present as an exact match in multiple studies recorded in dbVar. (kind: database_fact; confidence: high; evidence: DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008)
- A variant with high similarity to this insertion is recorded in gnomAD-SV at an allele frequency of 0.159. (kind: database_fact; confidence: high; evidence: GNO-BL-001)

## Clinical evidence and phenotype associations

No evidence recorded.

## Literature evidence

No evidence recorded.

## Possible interpretations

- The variant's placement within repeat-dense regions may compromise the reliability of the breakpoint coordinates. (kind: inference; confidence: medium; evidence: QC-BL-003)

## Qualified findings

No partially supported claims recorded.

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
- Baseline Ensembl annotations are based on coordinate overlap only and do not define functional impact.
- VEP consequences are computational predictions and do not reflect patient-specific transcript expression.
- Population database matches are provided as contextual evidence and do not prove the identity of the biological event.
- dbVar records are heterogeneous and potentially imprecise.
- Heuristic breakpoint window fallback is used for region queries in the absence of VCF confidence intervals.
- The dbVar and gnomAD-SV matches provide contextual population-level evidence and do not confirm clinical significance or biological identity.

## Recommended next steps

- Resolve evidence gap: No clinical significance data was identified in ClinVar.
- Resolve evidence gap: No dosage sensitivity information was applicable for this variant type.
- Resolve evidence gap: No specific literature was identified linking this intronic RHOA insertion to a phenotype.

## Evidence catalog

### dbVar

- **DBV-BL-001** (compatible; exact): dbVar nsv3552129: compatible submitted variant record.
  - Key facts: study_id="nstd152"; variant_types=["mobile element insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Merging"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3552129/
- **DBV-BL-002** (compatible; exact): dbVar nsv3947452: compatible submitted variant record.
  - Key facts: study_id="nstd167"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3947452/
- **DBV-BL-003** (compatible; exact): dbVar nsv4438715: compatible submitted variant record.
  - Key facts: study_id="nstd175"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv4438715/
- **DBV-BL-004** (compatible; exact): dbVar nsv5167875: compatible submitted variant record.
  - Key facts: study_id="nstd203"; variant_types=["mobile element insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5167875/
- **DBV-BL-005** (compatible; exact): dbVar nsv5535033: compatible submitted variant record.
  - Key facts: study_id="nstd206"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5535033/
- **DBV-BL-006** (compatible; exact): dbVar nsv5605727: compatible submitted variant record.
  - Key facts: study_id="nstd207"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Merging"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5605727/
- **DBV-BL-007** (compatible; exact): dbVar nsv5948684: compatible submitted variant record.
  - Key facts: study_id="nstd209"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5948684/
- **DBV-BL-008** (compatible; exact): dbVar nsv6062347: compatible submitted variant record.
  - Key facts: study_id="nstd212"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 387, "name": "RHOA"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="3:49404094-49404094"
  - Used by: population_evidence[1], verified_claims.C004
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6062347/
- **Source limitation:** dbVar aggregates submitter-defined variant regions and calls from many studies and technologies. Boundaries may be imprecise or remapped, a generic copy-number type may not establish DEL versus DUP direction, and this bounded endpoint search does not retrieve every enclosing record. A match is contextual evidence, not proof of event identity, clinical significance, or validation.

### Ensembl

- **ENS-BL-NOMINAL-GENE-002** (interval_overlap; region_overlap): gene RHOA found in the nominal region.
  - Key facts: feature_type="gene"; breakpoint_role="nominal"; external_name="RHOA"; id="ENSG00000067560"; biotype="protein_coding"; position="3:49359136-49412998"
  - Used by: gene_region_annotation[1], verified_claims.C001
- **ENS-BL-NOMINAL-REPEAT-001** (interval_overlap; region_overlap): repeat ENS-BL-NOMINAL-REPEAT-001 found in the nominal region.
  - Key facts: feature_type="repeat"; breakpoint_role="nominal"; position="3:49404019-49404313"
  - Used by: gene_region_annotation[3], verified_claims.C003
- **ENS-BL-NOMINAL-REPEAT-002** (interval_overlap; region_overlap): repeat ENS-BL-NOMINAL-REPEAT-002 found in the nominal region.
  - Key facts: feature_type="repeat"; breakpoint_role="nominal"; position="3:49404019-49404313"
  - Used by: gene_region_annotation[3], verified_claims.C003
- **Source limitation:** Spatial overlap only: sv_type is retained for provenance but does not change this query. Nominal-interval and breakpoint-window results are reported separately; a parsed BND mate is also queried separately. Each scope first combines gene, regulatory, and repeat features; a failed combined request falls back to serialized per-feature queries. A heuristic breakpoint window retrieves nearby features but is not a measured confidence interval. Results are capped per feature type; transcript, consequence, breakpoint, nearest-gene, and mappability annotation are not included. A null feature list means that feature query failed.

### gnomAD-SV

- **GNO-BL-001** (high_similarity): gnomAD-SV INS_chr3_9224a6a5 is a high_similarity match (AF=0.15904).
  - Key facts: variant_id="INS_chr3_9224a6a5"; type="INS"; af=0.15904; ac=17585; an=110570; filters=["HIGH_NCR"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 1, "start_within_allowed_window": true, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "comparison_scope": "insertion_point"}; position="3:49404094-49404095"
  - Used by: population_evidence[2], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/INS_chr3_9224a6a5?dataset=gnomad_sv_r4
- **Source limitation:** Similarity classes are deterministic screening labels, not proof of variant identity or biological effect. Heuristic windows are used only when VCF breakpoint confidence intervals are unavailable. BND records with a parsed mate are compared using both breakends and the chromosome pair, allowing reversed record order. Input orientation is retained but cannot be compared because it is absent from this gnomAD response. BND records without a mate retain first-breakend-only candidate matching. Adaptive retrieval padding, when nonzero, widens only the records retrieved from the API; it never widens the fixed matching windows. A gnomAD-SV absence does not establish novelty, pathogenicity, or technical validity.

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

- **VEP-BL-001** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000418115"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=true; mane_select="NM_001664.4"
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-002** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000422781"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-003** (modifier): VEP predicts intron_variant, non_coding_transcript_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000431929"; consequence_terms=["intron_variant", "non_coding_transcript_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-004** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000445425"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-005** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000454011"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-006** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000676712"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-007** (modifier): VEP predicts intron_variant, NMD_transcript_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000677684"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-008** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000678200"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-009** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000678921"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-010** (modifier): VEP predicts intron_variant for RHOA (MODIFIER).
  - Key facts: gene_symbol="RHOA"; gene_id="ENSG00000067560"; transcript_id="ENST00000679208"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/3:49404095-49404094:1/INS?canonical=1;mane=1;numbers=1
- **Source limitation:** VEP consequences are predictions for the submitted interval and symbolic allele. They do not establish expression change, dosage pathogenicity, phenotype, penetrance, or the actual transcript expressed in a sample. Only a ranked compact subset of consequences is retained.


## Query provenance

- Ensembl: found — {"query_region": "3:49404094-49404094", "query_strategy": "combined"}
- Ensembl VEP: found — {"query_region": "3:49404094-49404094"}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "3", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: not_applicable — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: not_found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [49403594, 49404594]}], "query_strategy": "expanded_full_interval"}
