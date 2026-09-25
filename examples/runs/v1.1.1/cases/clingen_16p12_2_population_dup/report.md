# Structural Variant Investigation Report

**Status:** complete

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
| Ensembl VEP | Found |
| gnomAD-SV | Found |
| ClinGen Dosage | Found |
| ClinVar | No record found |
| NCBI dbVar | Found |
| DGV Gold Standard | Found |

## Adaptive investigation

- Query budget used: 0/2
- Stop reason: Sufficient baseline evidence exists to classify the variant as a common population-based regional CNV without requiring additional transcript or gene queries.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The SV encompasses multiple genes, including MIR3680-1, SLC7A5P2, and various lncRNA/pseudogene transcripts, which are flagged for transcript amplification consequences by VEP. (kind: database_fact; confidence: high; evidence: ENS-BL-NOMINAL-GENE-001, ENS-BL-NOMINAL-GENE-003, VEP-BL-001, VEP-BL-002, VEP-BL-003, VEP-BL-004, VEP-BL-005, VEP-BL-006, VEP-BL-007, VEP-BL-008, VEP-BL-009, VEP-BL-010)

## Population and variant-database evidence

- The SV demonstrates partial or region overlap with numerous copy number variations (CNVs) in the dbVar database. (kind: database_fact; confidence: high; evidence: DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008, DBV-BL-009, DBV-BL-010)
- Multiple DGV Gold Standard gain variants exhibit partial overlap or region overlap with the query interval, indicating a frequency of 12.5% to 97% depending on the specific record. (kind: database_fact; confidence: high; evidence: DGV-BL-001, DGV-BL-002, DGV-BL-003, DGV-BL-004, DGV-BL-005, DGV-BL-006, DGV-BL-007)
- Several duplication variants were identified as candidates in gnomAD-SV with varying frequency, though similarity is limited to candidate spatial overlap. (kind: database_fact; confidence: high; evidence: GNO-BL-001, GNO-BL-002, GNO-BL-003, GNO-BL-004, GNO-BL-005, GNO-BL-006, GNO-BL-007, GNO-BL-008, GNO-BL-009, GNO-BL-010)

## Clinical evidence and phenotype associations

- The SV overlaps with ISCA-46691, a 16p12.2 population region indexed in ClinGen with no evidence for haploinsufficiency. (kind: database_fact; confidence: high; evidence: CGD-BL-001)

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
- Coordinate overlap does not equate to identical biological events.
- Population frequency in healthy individuals does not exclude the possibility of variable clinical penetrance.
- Baseline Ensembl annotations rely on coordinate overlap and do not define the specific transcript expressed in a given tissue.
- Heuristic window placement is for identification purposes and does not represent precise, experimentally verified break points.

## Recommended next steps

- Resolve evidence gap: No ClinVar records match the query interval, limiting known clinical aggregate interpretation.
- Resolve evidence gap: Functional impact of the duplication is not established; VEP consequences are predictive.
- Resolve evidence gap: Specific patient phenotype or clinical validation is absent.

## Evidence catalog

### ClinGen Dosage

- **CGD-BL-001** (curated_overlap; exact): ClinGen dosage record for 16p12.2 population region (DGV_Gold_Standard_June_2021_gssvG14372): curated_overlap.
  - Key facts: entity="16p12.2 population region (DGV_Gold_Standard_June_2021_gssvG14372)"; entity_type="region"; relevant_dosage_direction="triplosensitivity"; haploinsufficiency={"assessment": "No Evidence for Haploinsufficiency", "score": 0}; triplosensitivity={"assessment": "", "score": null}; position="16:21500755-21584256"
  - Used by: clinical_phenotype_evidence[1], verified_claims.C001
  - Source: https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-46691
- **Source limitation:** ClinGen dosage scores are expert-curated gene/region evidence, not a patient-level classification. Coordinate overlap does not establish that recurrent breakpoints, copy state, phenotype, inheritance, or structural configuration match the curated cases.

### dbVar

- **DBV-BL-001** (ambiguous_cnv_direction; partial_overlap): dbVar nsv6507443: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd223"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 646828, "name": "LOC646828"}, {"id": 100500917, "name": "MIR3680-1"}, {"id": 387254, "name": "SLC7A5P2"}, {"id": 100271836, "name": "SMG1P3"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 546, "end_offset_bp": 44, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.993461, "reciprocal_overlap_database": 0.99947, "size_similarity": 0.993988}; position="16:21501301-21584300"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6507443/
- **DBV-BL-002** (ambiguous_cnv_direction; partial_overlap): dbVar nsv6509590: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd223"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 100500917, "name": "MIR3680-1"}, {"id": 100271836, "name": "SMG1P3"}, {"id": 387254, "name": "SLC7A5P2"}, {"id": 646828, "name": "LOC646828"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 1046, "end_offset_bp": 44, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.987473, "reciprocal_overlap_database": 0.999467, "size_similarity": 0.988}; position="16:21501801-21584300"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6509590/
- **DBV-BL-003** (ambiguous_cnv_direction; partial_overlap): dbVar nsv6499184: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd223"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 646828, "name": "LOC646828"}, {"id": 387254, "name": "SLC7A5P2"}, {"id": 100271836, "name": "SMG1P3"}, {"id": 100500917, "name": "MIR3680-1"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": -454, "end_offset_bp": -1156, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.986156, "reciprocal_overlap_database": 0.994517, "size_similarity": 0.991593}; position="16:21500301-21583100"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6499184/
- **DBV-BL-004** (ambiguous_cnv_direction; partial_overlap): dbVar nsv6501992: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd223"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 51108, "name": "METTL9"}, {"id": 646828, "name": "LOC646828"}, {"id": 100271836, "name": "SMG1P3"}, {"id": 100500917, "name": "MIR3680-1"}, {"id": 101927814, "name": "LOC101927814"}, {"id": 387254, "name": "SLC7A5P2"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 646, "end_offset_bp": 16144, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.992264, "reciprocal_overlap_database": 0.836929, "size_similarity": 0.843455}; position="16:21501401-21600400"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6501992/
- **DBV-BL-005** (ambiguous_cnv_direction; partial_overlap): dbVar nsv6511878: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd223"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 646828, "name": "LOC646828"}, {"id": 100500917, "name": "MIR3680-1"}, {"id": 387254, "name": "SLC7A5P2"}, {"id": 100271836, "name": "SMG1P3"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": -22454, "end_offset_bp": -5556, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.933463, "reciprocal_overlap_database": 0.776355, "size_similarity": 0.831693}; position="16:21478301-21578700"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6511878/
- **DBV-BL-006** (ambiguous_cnv_direction; partial_overlap): dbVar nsv7685969: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd239"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 387254, "name": "SLC7A5P2"}, {"id": 646828, "name": "LOC646828"}]; methods=["SNP array"]; match_metrics={"start_offset_bp": 7038, "end_offset_bp": -25851, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.606129, "reciprocal_overlap_database": 1.0, "size_similarity": 0.606129}; position="16:21507793-21558405"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7685969/
- **DBV-BL-007** (ambiguous_cnv_direction; region_overlap): dbVar nsv6983400: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd229"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; methods=["Sequencing"]; match_metrics={"start_offset_bp": 53182, "end_offset_bp": -20691, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.115315, "reciprocal_overlap_database": 1.0, "size_similarity": 0.115315}; position="16:21553937-21563565"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6983400/
- **DBV-BL-008** (ambiguous_cnv_direction; region_overlap): dbVar nsv6997950: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd229"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; methods=["Sequencing"]; match_metrics={"start_offset_bp": 54202, "end_offset_bp": -22567, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.080633, "reciprocal_overlap_database": 1.0, "size_similarity": 0.080633}; position="16:21554957-21561689"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6997950/
- **DBV-BL-009** (ambiguous_cnv_direction; region_overlap): dbVar nsv6503113: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd223"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; methods=["Sequencing"]; match_metrics={"start_offset_bp": 75587, "end_offset_bp": -6463, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.017389, "reciprocal_overlap_database": 1.0, "size_similarity": 0.017389}; position="16:21576342-21577793"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6503113/
- **DBV-BL-010** (ambiguous_cnv_direction; region_overlap): dbVar nsv7693200: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd239"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 51108, "name": "METTL9"}, {"id": 101927814, "name": "LOC101927814"}]; methods=["SNP array"]; match_metrics={"start_offset_bp": 66312, "end_offset_bp": 16985, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.205863, "reciprocal_overlap_database": 0.502999, "size_similarity": 0.409272}; position="16:21567067-21601241"
  - Used by: population_evidence[1], verified_claims.C002
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7693200/
- **Source limitation:** dbVar aggregates submitter-defined variant regions and calls from many studies and technologies. Boundaries may be imprecise or remapped, a generic copy-number type may not establish DEL versus DUP direction, and this bounded endpoint search does not retrieve every enclosing record. A match is contextual evidence, not proof of event identity, clinical significance, or validation.

### DGV Gold

- **DGV-BL-001** (partial_overlap): DGV Gold gssvG14123: partial_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Gain"; frequency="12.5%"; num_unique_samples_tested=32; num_samples_with_variant=4; num_studies=3; match_metrics={"start_offset_bp": 17615, "end_offset_bp": -1177, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.774951, "reciprocal_overlap_database": 1.0, "size_similarity": 0.774951}; position="16:21518370-21583079"
  - Used by: population_evidence[2], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21518369;end=21583079
- **DGV-BL-002** (partial_overlap): DGV Gold gssvG14113: partial_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Gain"; frequency="18.8652%"; num_unique_samples_tested=1410; num_samples_with_variant=266; num_studies=6; match_metrics={"start_offset_bp": -30931, "end_offset_bp": 14989, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.645192, "size_similarity": 0.645192}; position="16:21469824-21599245"
  - Used by: population_evidence[2], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21469823;end=21599245
- **DGV-BL-003** (region_overlap): DGV Gold gssvG14136: region_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Gain"; frequency="97.2951%"; num_unique_samples_tested=2514; num_samples_with_variant=2446; num_studies=2; match_metrics={"start_offset_bp": 29609, "end_offset_bp": -25283, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.342627, "reciprocal_overlap_database": 1.0, "size_similarity": 0.342627}; position="16:21530364-21558973"
  - Used by: population_evidence[2], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21530363;end=21558973
- **DGV-BL-004** (region_overlap): DGV Gold gssvG14147: region_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Gain"; frequency="72.4279%"; num_unique_samples_tested=3674; num_samples_with_variant=2661; num_studies=3; match_metrics={"start_offset_bp": 57103, "end_offset_bp": -13443, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.155158, "reciprocal_overlap_database": 1.0, "size_similarity": 0.155158}; position="16:21557858-21570813"
  - Used by: population_evidence[2], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21557857;end=21570813
- **DGV-BL-005** (region_overlap): DGV Gold gssvG14107: region_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Gain"; frequency="13.6986%"; num_unique_samples_tested=73; num_samples_with_variant=10; num_studies=3; match_metrics={"start_offset_bp": -146521, "end_offset_bp": 7792, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.351122, "size_similarity": 0.351122}; position="16:21354234-21592048"
  - Used by: population_evidence[2], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21354233;end=21592048
- **DGV-BL-006** (region_overlap): DGV Gold gssvG14106: region_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Gain"; frequency="0.111337%"; num_unique_samples_tested=15269; num_samples_with_variant=17; num_studies=4; match_metrics={"start_offset_bp": 22228, "end_offset_bp": 243763, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.733803, "reciprocal_overlap_database": 0.200874, "size_similarity": 0.273744}; position="16:21522983-21828019"
  - Used by: population_evidence[2], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21522982;end=21828019
- **DGV-BL-007** (region_overlap): DGV Gold gssvG14104: region_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Gain"; frequency="0.135542%"; num_unique_samples_tested=13280; num_samples_with_variant=18; num_studies=5; match_metrics={"start_offset_bp": -151774, "end_offset_bp": 350770, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.142484, "size_similarity": 0.142484}; position="16:21348981-21935026"
  - Used by: population_evidence[2], verified_claims.C004
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr16;start=21348980;end=21935026
- **Source limitation:** This adapter queries the curated DGV Gold Standard track exposed by UCSC, not the complete current DGV release. DGV aggregates healthy-control studies with heterogeneous platforms and often imprecise boundaries. Overlap or frequency is contextual population evidence, not proof of the same event, benignity, or absence of clinical effect.

### Ensembl

- **ENS-BL-NOMINAL-GENE-001** (interval_overlap; region_overlap): gene MIR3680-1 found in the nominal region.
  - Key facts: feature_type="gene"; breakpoint_role="nominal"; external_name="MIR3680-1"; id="ENSG00000265462"; biotype="miRNA"; position="16:21506049-21506135"
  - Used by: gene_region_annotation[1], verified_claims.C003
- **ENS-BL-NOMINAL-GENE-003** (interval_overlap; region_overlap): gene SLC7A5P2 found in the nominal region.
  - Key facts: feature_type="gene"; breakpoint_role="nominal"; external_name="SLC7A5P2"; id="ENSG00000258186"; biotype="transcribed_processed_pseudogene"; position="16:21519830-21520365"
  - Used by: gene_region_annotation[1], verified_claims.C003
- **Source limitation:** Spatial overlap only: sv_type is retained for provenance but does not change this query. Nominal-interval and breakpoint-window results are reported separately; a parsed BND mate is also queried separately. Each scope first combines gene, regulatory, and repeat features; a failed combined request falls back to serialized per-feature queries. A heuristic breakpoint window retrieves nearby features but is not a measured confidence interval. Results are capped per feature type; transcript, consequence, breakpoint, nearest-gene, and mappability annotation are not included. A null feature list means that feature query failed.

### gnomAD-SV

- **GNO-BL-001** (region_overlap): gnomAD-SV DUP_chr16_7371ee55 is a region_overlap match (AF=0.000159).
  - Key facts: variant_id="DUP_chr16_7371ee55"; type="DUP"; af=0.000159; ac=20; an=126092; match_metrics={"start_offset_bp": 75323, "end_offset_bp": -7291, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.010634, "reciprocal_overlap_database": 1.0, "size_similarity": 0.010634}; position="16:21576078-21576965"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_7371ee55?dataset=gnomad_sv_r4
- **GNO-BL-002** (region_overlap): gnomAD-SV DUP_chr16_6602690e is a region_overlap match (AF=0.555621).
  - Key facts: variant_id="DUP_chr16_6602690e"; type="DUP"; af=0.555621; ac=25363; an=45648; filters=["HIGH_NCR"]; match_metrics={"start_offset_bp": -4269, "end_offset_bp": -78363, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.061543, "reciprocal_overlap_database": 0.546237, "size_similarity": 0.112668}; position="16:21496486-21505893"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_6602690e?dataset=gnomad_sv_r4
- **GNO-BL-003** (region_overlap): gnomAD-SV DUP_chr16_893590be is a region_overlap match (AF=4.8e-05).
  - Key facts: variant_id="DUP_chr16_893590be"; type="DUP"; af=4.8e-05; ac=6; an=125994; match_metrics={"start_offset_bp": 23958, "end_offset_bp": -58967, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.00691, "reciprocal_overlap_database": 1.0, "size_similarity": 0.00691}; position="16:21524713-21525289"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_893590be?dataset=gnomad_sv_r4
- **GNO-BL-004** (region_overlap): gnomAD-SV DUP_chr16_d5cb8295 is a region_overlap match (AF=5.6e-05).
  - Key facts: variant_id="DUP_chr16_d5cb8295"; type="DUP"; af=5.6e-05; ac=7; an=125170; match_metrics={"start_offset_bp": 72034, "end_offset_bp": -11259, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.002503, "reciprocal_overlap_database": 1.0, "size_similarity": 0.002503}; position="16:21572789-21572997"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_d5cb8295?dataset=gnomad_sv_r4
- **GNO-BL-005** (region_overlap): gnomAD-SV DUP_chr16_5b11758f is a region_overlap match (AF=4.9e-05).
  - Key facts: variant_id="DUP_chr16_5b11758f"; type="DUP"; af=4.9e-05; ac=6; an=121528; match_metrics={"start_offset_bp": 6789, "end_offset_bp": -76628, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.001018, "reciprocal_overlap_database": 1.0, "size_similarity": 0.001018}; position="16:21507544-21507628"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_5b11758f?dataset=gnomad_sv_r4
- **GNO-BL-006** (region_overlap): gnomAD-SV DUP_chr16_9e3b66dd is a region_overlap match (AF=8e-06).
  - Key facts: variant_id="DUP_chr16_9e3b66dd"; type="DUP"; af=8e-06; ac=1; an=126088; match_metrics={"start_offset_bp": 73116, "end_offset_bp": -10317, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.000826, "reciprocal_overlap_database": 1.0, "size_similarity": 0.000826}; position="16:21573871-21573939"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_9e3b66dd?dataset=gnomad_sv_r4
- **GNO-BL-007** (region_overlap): gnomAD-SV DUP_chr16_494000a2 is a region_overlap match (AF=2.4e-05).
  - Key facts: variant_id="DUP_chr16_494000a2"; type="DUP"; af=2.4e-05; ac=3; an=126086; match_metrics={"start_offset_bp": 40249, "end_offset_bp": -43191, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.000742, "reciprocal_overlap_database": 1.0, "size_similarity": 0.000742}; position="16:21541004-21541065"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_494000a2?dataset=gnomad_sv_r4
- **GNO-BL-008** (region_overlap): gnomAD-SV DUP_chr16_e2083be9 is a region_overlap match (AF=0.000111).
  - Key facts: variant_id="DUP_chr16_e2083be9"; type="DUP"; af=0.000111; ac=14; an=126086; match_metrics={"start_offset_bp": 63816, "end_offset_bp": -19627, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.000707, "reciprocal_overlap_database": 1.0, "size_similarity": 0.000707}; position="16:21564571-21564629"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_e2083be9?dataset=gnomad_sv_r4
- **GNO-BL-009** (region_overlap): gnomAD-SV DUP_chr16_ac985419 is a region_overlap match (AF=0.000786).
  - Key facts: variant_id="DUP_chr16_ac985419"; type="DUP"; af=0.000786; ac=97; an=123444; match_metrics={"start_offset_bp": 80988, "end_offset_bp": 6230, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.030107, "reciprocal_overlap_database": 0.287511, "size_similarity": 0.104716}; position="16:21581743-21590486"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_ac985419?dataset=gnomad_sv_r4
- **GNO-BL-010** (region_overlap): gnomAD-SV DUP_chr16_5f3f07b6 is a region_overlap match (AF=1.6e-05).
  - Key facts: variant_id="DUP_chr16_5f3f07b6"; type="DUP"; af=1.6e-05; ac=2; an=125970; match_metrics={"start_offset_bp": 81731, "end_offset_bp": 42230, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 0.021209, "reciprocal_overlap_database": 0.040249, "size_similarity": 0.526945}; position="16:21582486-21626486"
  - Used by: population_evidence[3], verified_claims.C005
  - Source: https://gnomad.broadinstitute.org/variant/DUP_chr16_5f3f07b6?dataset=gnomad_sv_r4
- **Source limitation:** Similarity classes are deterministic screening labels, not proof of variant identity or biological effect. Heuristic windows are used only when VCF breakpoint confidence intervals are unavailable. BND records with a parsed mate are compared using both breakends and the chromosome pair, allowing reversed record order. Input orientation is retained but cannot be compared because it is absent from this gnomAD response. BND records without a mate retain first-breakend-only candidate matching. Adaptive retrieval padding, when nonzero, widens only the records retrieved from the API; it never widens the fixed matching windows. A gnomAD-SV absence does not establish novelty, pathogenicity, or technical validity.

### Artifact-risk rules

- **QC-BL-001** (unknown): low_call_rate: unknown. Missingness can produce spurious population differences.
  - Key facts: risk_type="low_call_rate"; recommended_check="Calculate call rate per cohort."
  - Used by: artifact_risks.low_call_rate
- **QC-BL-002** (unknown): single_caller_support: unknown. A call from one algorithm may reflect caller-specific bias.
  - Key facts: risk_type="single_caller_support"; recommended_check="Validate with an orthogonal caller or experimental assay."
  - Used by: artifact_risks.single_caller_support
- **QC-BL-003** (present): repeat_region: present. Repeats in breakpoint windows can make breakpoint placement unreliable.
  - Key facts: risk_type="repeat_region"; evidence={"scope": "breakpoint_windows", "start_repeat_count": 3, "end_repeat_count": 10}; recommended_check="Confirm both breakpoints against a curated repeat track."
  - Used by: artifact_risks.repeat_region
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

- **VEP-BL-001** (high): VEP predicts transcript_amplification for ENST00000550637 (HIGH).
  - Key facts: gene_id="ENSG00000257639"; transcript_id="ENST00000550637"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-002** (high): VEP predicts transcript_amplification for SLC7A5P2 (HIGH).
  - Key facts: gene_symbol="SLC7A5P2"; gene_id="ENSG00000258186"; transcript_id="ENST00000553010"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-003** (high): VEP predicts transcript_amplification for MIR3680-1 (HIGH).
  - Key facts: gene_symbol="MIR3680-1"; gene_id="ENSG00000265462"; transcript_id="ENST00000581433"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-004** (high): VEP predicts transcript_amplification for ENST00000605544 (HIGH).
  - Key facts: gene_id="ENSG00000271609"; transcript_id="ENST00000605544"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-005** (high): VEP predicts transcript_amplification for ENST00000654954 (HIGH).
  - Key facts: gene_id="ENSG00000287809"; transcript_id="ENST00000654954"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-006** (high): VEP predicts transcript_amplification for ENST00000766133 (HIGH).
  - Key facts: gene_id="ENSG00000273956"; transcript_id="ENST00000766133"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-007** (high): VEP predicts transcript_amplification for ENST00000766304 (HIGH).
  - Key facts: gene_id="ENSG00000299776"; transcript_id="ENST00000766304"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-008** (high): VEP predicts transcript_amplification for ENST00000790193 (HIGH).
  - Key facts: gene_id="ENSG00000302877"; transcript_id="ENST00000790193"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-009** (high): VEP predicts transcript_amplification for ENST00000811682 (HIGH).
  - Key facts: gene_id="ENSG00000305553"; transcript_id="ENST00000811682"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **VEP-BL-010** (high): VEP predicts transcript_amplification for ENST00000811758 (HIGH).
  - Key facts: gene_id="ENSG00000305577"; transcript_id="ENST00000811758"; consequence_terms=["transcript_amplification"]; impact="HIGH"; percentage_overlap=100; canonical=true
  - Used by: gene_region_annotation[1], verified_claims.C003
  - Source: https://rest.ensembl.org/vep/human/region/16:21500755-21584256:1/DUP?canonical=1;mane=1;numbers=1
- **Source limitation:** VEP consequences are predictions for the submitted interval and symbolic allele. They do not establish expression change, dosage pathogenicity, phenotype, penetrance, or the actual transcript expressed in a sample. Only a ranked compact subset of consequences is retained.


## Query provenance

- Ensembl: found — {"query_region": "16:21500755-21584256", "query_strategy": "combined"}
- Ensembl VEP: found — {"query_region": "16:21500755-21584256"}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "16", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: found — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [21500255, 21584756]}], "query_strategy": "expanded_full_interval"}
