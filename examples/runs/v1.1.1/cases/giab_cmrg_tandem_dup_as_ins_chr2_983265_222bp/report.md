# Structural Variant Investigation Report

**Status:** complete

## Variant summary

| Field | Value |
|---|---|
| SV ID | `GIAB_CMRG_GRCh38_chr2_983265_INS222_REPTYPE_DUP` |
| Reference build | GRCh38 |
| Position | chr2:983265-983265 |
| SV type | INS |
| Coordinate system | 1-based-inclusive |
| Length | 222 bp |
| Breakpoint uncertainty | not_provided; start CI=not provided; end CI=not provided |

## Baseline source checks

| Database or resource | Result |
|---|---|
| Ensembl | Found |
| Ensembl VEP | Found |
| gnomAD-SV | No record found |
| ClinGen Dosage | Not applicable |
| ClinVar | No record found |
| NCBI dbVar | Found |
| DGV Gold Standard | No record found |

## Adaptive investigation

- Query budget used: 0/2
- Stop reason: The baseline evidence is sufficient to characterize the variant as an intronic insertion in the SNTG2 gene, with consistent dbVar records, and further queries would not yield information that changes the interpretation.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The insertion variant is located within an intron of the SNTG2 gene (ENSG00000172554). (kind: database_fact; confidence: high; evidence: VEP-BL-001, VEP-BL-002, VEP-BL-003, VEP-BL-004, VEP-BL-005, VEP-BL-006, VEP-BL-007, VEP-BL-008, VEP-BL-009, VEP-BL-010)
- The variant site intersects with identified tandem repeat features in the GRCh38 genome assembly. (kind: observation; confidence: high; evidence: ENS-BL-NOMINAL-REPEAT-001, ENS-BL-NOMINAL-REPEAT-002, ENS-BL-START-REPEAT-001, ENS-BL-START-REPEAT-002, ENS-BL-START-REPEAT-003, ENS-BL-START-REPEAT-004, ENS-BL-START-REPEAT-005, ENS-BL-START-REPEAT-006, QC-BL-003)

## Population and variant-database evidence

- Multiple studies have submitted variant records in the dbVar database that overlap or occur near the variant coordinates. (kind: database_fact; confidence: high; evidence: DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008, DBV-BL-009, DBV-BL-010)

## Clinical evidence and phenotype associations

No evidence recorded.

## Literature evidence

No evidence recorded.

## Possible interpretations

No evidence recorded.

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
- The presence of repeat sequences at the breakpoint region may introduce technical ambiguity in variant calling and alignment.
- Database records in dbVar are heterogeneous and do not establish the clinical or functional equivalence of this specific SV.
- VEP consequence predictions for an SV allele do not confirm any actual impact on gene expression or protein function.
- Repeat sequence presence at breakpoint may cause alignment and calling ambiguity.
- Database matches do not imply functional or clinical equivalence.

## Recommended next steps

- Resolve evidence gap: No specific clinical or functional literature was identified for this variant or structural variants within the SNTG2 gene in the provided search scope.
- Resolve evidence gap: No ClinVar records were found, leaving the clinical significance of this locus uncharacterized by public clinical databases.

## Evidence catalog

### dbVar

- **DBV-BL-001** (compatible; exact): dbVar esv3656833: compatible submitted variant record.
  - Key facts: study_id="estd217"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="2:983265-983265"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3656833/
- **DBV-BL-002** (compatible; exact): dbVar nsv3953858: compatible submitted variant record.
  - Key facts: study_id="nstd167"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="2:983265-983265"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3953858/
- **DBV-BL-003** (compatible; exact): dbVar nsv5618433: compatible submitted variant record.
  - Key facts: study_id="nstd207"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Merging"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="2:983265-983265"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5618433/
- **DBV-BL-004** (compatible; exact): dbVar nsv5961524: compatible submitted variant record.
  - Key facts: study_id="nstd209"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="2:983265-983265"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5961524/
- **DBV-BL-005** (compatible; exact): dbVar nsv6053736: compatible submitted variant record.
  - Key facts: study_id="nstd212"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="2:983265-983265"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6053736/
- **DBV-BL-006** (compatible; exact): dbVar nsv6220675: compatible submitted variant record.
  - Key facts: study_id="nstd214"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="2:983265-983265"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6220675/
- **DBV-BL-007** (compatible; exact): dbVar nsv7862737: compatible submitted variant record.
  - Key facts: study_id="nstd232"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="2:983265-983265"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7862737/
- **DBV-BL-008** (compatible; nearby): dbVar nsv2806727: compatible submitted variant record.
  - Key facts: study_id="nstd137"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 1, "end_offset_bp": 1, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.0, "reciprocal_overlap_database": 0.0, "size_similarity": 1.0}; position="2:983266-983266"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv2806727/
- **DBV-BL-009** (compatible; nearby): dbVar nsv3366452: compatible submitted variant record.
  - Key facts: study_id="nstd162"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 1, "end_offset_bp": 1, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.0, "reciprocal_overlap_database": 0.0, "size_similarity": 1.0}; position="2:983266-983266"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3366452/
- **DBV-BL-010** (compatible; nearby): dbVar nsv3377346: compatible submitted variant record.
  - Key facts: study_id="nstd162"; variant_types=["insertion"]; type_compatibility="compatible"; genes=[{"id": 54221, "name": "SNTG2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 1, "end_offset_bp": 1, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.0, "reciprocal_overlap_database": 0.0, "size_similarity": 1.0}; position="2:983266-983266"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3377346/
- **Source limitation:** dbVar aggregates submitter-defined variant regions and calls from many studies and technologies. Boundaries may be imprecise or remapped, a generic copy-number type may not establish DEL versus DUP direction, and this bounded endpoint search does not retrieve every enclosing record. A match is contextual evidence, not proof of event identity, clinical significance, or validation.

### Ensembl

- **ENS-BL-NOMINAL-REPEAT-001** (interval_overlap; region_overlap): repeat ENS-BL-NOMINAL-REPEAT-001 found in the nominal region.
  - Key facts: feature_type="repeat"; breakpoint_role="nominal"; position="2:982975-983420"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **ENS-BL-NOMINAL-REPEAT-002** (interval_overlap; region_overlap): repeat ENS-BL-NOMINAL-REPEAT-002 found in the nominal region.
  - Key facts: feature_type="repeat"; breakpoint_role="nominal"; position="2:983007-983420"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **ENS-BL-START-REPEAT-001** (breakpoint_window_hit; region_overlap): repeat ENS-BL-START-REPEAT-001 found in the start region.
  - Key facts: feature_type="repeat"; breakpoint_role="start"; position="2:982921-983245"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **ENS-BL-START-REPEAT-002** (breakpoint_window_hit; region_overlap): repeat ENS-BL-START-REPEAT-002 found in the start region.
  - Key facts: feature_type="repeat"; breakpoint_role="start"; position="2:982946-983093"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **ENS-BL-START-REPEAT-003** (breakpoint_window_hit; region_overlap): repeat ENS-BL-START-REPEAT-003 found in the start region.
  - Key facts: feature_type="repeat"; breakpoint_role="start"; position="2:982946-983093"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **ENS-BL-START-REPEAT-004** (breakpoint_window_hit; region_overlap): repeat ENS-BL-START-REPEAT-004 found in the start region.
  - Key facts: feature_type="repeat"; breakpoint_role="start"; position="2:982975-983420"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **ENS-BL-START-REPEAT-005** (breakpoint_window_hit; region_overlap): repeat ENS-BL-START-REPEAT-005 found in the start region.
  - Key facts: feature_type="repeat"; breakpoint_role="start"; position="2:983007-983420"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **ENS-BL-START-REPEAT-006** (breakpoint_window_hit; region_overlap): repeat ENS-BL-START-REPEAT-006 found in the start region.
  - Key facts: feature_type="repeat"; breakpoint_role="start"; position="2:983292-983380"
  - Used by: gene_region_annotation[2], verified_claims.C002
- **Source limitation:** Spatial overlap only: sv_type is retained for provenance but does not change this query. Nominal-interval and breakpoint-window results are reported separately; a parsed BND mate is also queried separately. Each scope first combines gene, regulatory, and repeat features; a failed combined request falls back to serialized per-feature queries. A heuristic breakpoint window retrieves nearby features but is not a measured confidence interval. Results are capped per feature type; transcript, consequence, breakpoint, nearest-gene, and mappability annotation are not included. A null feature list means that feature query failed.

### Artifact-risk rules

- **QC-BL-001** (unknown): low_call_rate: unknown. Missingness can produce spurious population differences.
  - Key facts: risk_type="low_call_rate"; recommended_check="Calculate call rate per cohort."
  - Used by: artifact_risks.low_call_rate
- **QC-BL-002** (unknown): single_caller_support: unknown. A call from one algorithm may reflect caller-specific bias.
  - Key facts: risk_type="single_caller_support"; recommended_check="Validate with an orthogonal caller or experimental assay."
  - Used by: artifact_risks.single_caller_support
- **QC-BL-003** (present): repeat_region: present. Repeats in breakpoint windows can make breakpoint placement unreliable.
  - Key facts: risk_type="repeat_region"; evidence={"scope": "breakpoint_windows", "start_repeat_count": 6, "end_repeat_count": 6}; recommended_check="Confirm both breakpoints against a curated repeat track."
  - Used by: gene_region_annotation[2], artifact_risks.repeat_region, verified_claims.C002
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

- **VEP-BL-001** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000308624"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=true; mane_select="NM_018968.4"
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-002** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000407292"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-003** (modifier): VEP predicts intron_variant, NMD_transcript_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000450962"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-004** (modifier): VEP predicts intron_variant, NMD_transcript_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000452177"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-005** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000912579"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-006** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000912580"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-007** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000912581"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-008** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000912582"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-009** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000912583"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-010** (modifier): VEP predicts intron_variant for SNTG2 (MODIFIER).
  - Key facts: gene_symbol="SNTG2"; gene_id="ENSG00000172554"; transcript_id="ENST00000941025"; consequence_terms=["intron_variant"]; impact="MODIFIER"; canonical=false
  - Used by: gene_region_annotation[1], verified_claims.C001
  - Source: https://rest.ensembl.org/vep/human/region/2:983266-983265:1/INS?canonical=1;mane=1;numbers=1
- **Source limitation:** VEP consequences are predictions for the submitted interval and symbolic allele. They do not establish expression change, dosage pathogenicity, phenotype, penetrance, or the actual transcript expressed in a sample. Only a ranked compact subset of consequences is retained.


## Query provenance

- Ensembl: found — {"query_region": "2:983265-983265", "query_strategy": "combined"}
- Ensembl VEP: found — {"query_region": "2:983265-983265"}
- gnomAD-SV: not_found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "2", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: not_applicable — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: not_found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- PubMed: not_found — SNTG2 insertion chr2:983265
- PubMed: not_found — "SNTG2" SV insertion
