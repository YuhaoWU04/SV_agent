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
- Stop reason: The variant is a small 50bp deletion in an intronic region of RNF212. Baseline evidence, including high-frequency gnomAD records, indicates it is a common polymorphism. Further investigation into transcripts or genes is unlikely to change the interpretation as the variant is clearly non-coding and well-represented in population databases.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The variant is a 50bp deletion located within the gene RNF212. (kind: observation; confidence: high; evidence: ENS-BL-NOMINAL-GENE-001, VEP-BL-001)
- VEP predicts this variant is an intronic modifier for multiple RNF212 transcript isoforms. (kind: database_fact; confidence: high; evidence: VEP-BL-001, VEP-BL-002, VEP-BL-003, VEP-BL-004, VEP-BL-005, VEP-BL-006, VEP-BL-007, VEP-BL-008, VEP-BL-009, VEP-BL-010)

## Population and variant-database evidence

- This variant (or partial overlaps) is reported in multiple databases, including gnomAD-SV, dbVar, and the DGV Gold Standard track. (kind: database_fact; confidence: high; evidence: GNO-BL-001, DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008, DBV-BL-009, DBV-BL-010, DGV-BL-001)

## Clinical evidence and phenotype associations

No evidence recorded.

## Literature evidence

No evidence recorded.

## Possible interpretations

- The functional impact of this specific 50bp intronic deletion on RNF212 expression or recombination phenotypes is unknown. (kind: inference; confidence: medium; evidence: none)

## Qualified findings

- RNF212 is associated with recombination rate variation across different species. (evidence: PMID-22844258, PMID-24390283, PMID-27516620, PMID-35596132, PMID-41565805; qualification: Only PubMed citation metadata was retrieved; full-text support was not checked.)

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
- VEP consequences are prediction-based and do not indicate actual biological impact or expression changes.
- Database records (gnomAD, dbVar, DGV) indicate candidate overlaps, not proof of identity or significance.
- Breakpoint window QC flags indicate potential issues with placement due to repetitive sequences.
- No clinical dosage sensitivity records are available for this region from ClinGen.
- No specific evidence in ClinVar links this variant to clinical phenotypes.
- VEP consequences are prediction-based and do not indicate actual biological impact.
- Database records indicate candidate positional overlaps, not proof of identity.
- Breakpoint window QC flags suggest potential placement uncertainty due to repetitive sequences.
- Conservatively qualified claim C004: Only PubMed citation metadata was retrieved; full-text support was not checked.

## Recommended next steps

- Resolve evidence gap: No clinical dosage sensitivity records are available for this region from ClinGen.
- Resolve evidence gap: No specific evidence in ClinVar links this variant to clinical phenotypes.
- Resolve evidence gap: Lack of direct literature linking this specific 50bp intronic deletion to meiotic recombination rates.

## Evidence catalog

### dbVar

- **DBV-BL-001** (ambiguous_cnv_direction; exact): dbVar esv3833873: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="estd219"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Merging"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="4:1092990-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3833873/
- **DBV-BL-002** (ambiguous_cnv_direction; exact): dbVar nsv2809287: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd137"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="4:1092990-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv2809287/
- **DBV-BL-003** (ambiguous_cnv_direction; exact): dbVar nsv3392756: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd162"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="4:1092990-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3392756/
- **DBV-BL-004** (ambiguous_cnv_direction; exact): dbVar nsv4390961: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd171"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Merging"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="4:1092990-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv4390961/
- **DBV-BL-005** (ambiguous_cnv_direction; exact): dbVar nsv4651823: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="nstd186"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Curated"]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 0, "start_within_allowed_window": true, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 1.0, "size_similarity": 1.0}; position="4:1092990-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv4651823/
- **DBV-BL-006** (ambiguous_cnv_direction; partial_overlap): dbVar dsv2402: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="dstd1"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": -1, "end_offset_bp": 0, "start_within_allowed_window": false, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.980392, "size_similarity": 0.980392}; position="4:1092989-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/dsv2402/
- **DBV-BL-007** (ambiguous_cnv_direction; partial_overlap): dbVar esv1191684: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="estd22"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": -1, "end_offset_bp": 0, "start_within_allowed_window": false, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.980392, "size_similarity": 0.980392}; position="4:1092989-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/esv1191684/
- **DBV-BL-008** (ambiguous_cnv_direction; partial_overlap): dbVar esv3046033: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="estd209"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": -1, "end_offset_bp": 0, "start_within_allowed_window": false, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.980392, "size_similarity": 0.980392}; position="4:1092989-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3046033/
- **DBV-BL-009** (ambiguous_cnv_direction; partial_overlap): dbVar esv3494989: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="estd59"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; match_metrics={"start_offset_bp": 0, "end_offset_bp": 1, "start_within_allowed_window": true, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.980392, "size_similarity": 0.980392}; position="4:1092990-1093040"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3494989/
- **DBV-BL-010** (ambiguous_cnv_direction; partial_overlap): dbVar esv3563229: ambiguous_cnv_direction submitted variant record.
  - Key facts: study_id="estd215"; variant_types=["copy number variation"]; type_compatibility="ambiguous_cnv_direction"; genes=[{"id": 285498, "name": "RNF212"}]; methods=["Sequencing"]; match_metrics={"start_offset_bp": -1, "end_offset_bp": 0, "start_within_allowed_window": false, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.980392, "size_similarity": 0.980392}; position="4:1092989-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3563229/
- **Source limitation:** dbVar aggregates submitter-defined variant regions and calls from many studies and technologies. Boundaries may be imprecise or remapped, a generic copy-number type may not establish DEL versus DUP direction, and this bounded endpoint search does not retrieve every enclosing record. A match is contextual evidence, not proof of event identity, clinical significance, or validation.

### DGV Gold

- **DGV-BL-001** (partial_overlap): DGV Gold gssvL87089: partial_overlap population CNV record.
  - Key facts: variant_type="CNV"; variant_sub_type="Loss"; frequency="0.462963%"; num_unique_samples_tested=864; num_samples_with_variant=4; num_studies=3; match_metrics={"start_offset_bp": -1, "end_offset_bp": 19, "start_within_allowed_window": false, "end_within_allowed_window": false, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.714286, "size_similarity": 0.714286}; position="4:1092989-1093058"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr4;start=1092988;end=1093058
- **Source limitation:** This adapter queries the curated DGV Gold Standard track exposed by UCSC, not the complete current DGV release. DGV aggregates healthy-control studies with heterogeneous platforms and often imprecise boundaries. Overlap or frequency is contextual population evidence, not proof of the same event, benignity, or absence of clinical effect.

### Ensembl

- **ENS-BL-NOMINAL-GENE-001** (interval_overlap; region_overlap): gene RNF212 found in the nominal region.
  - Key facts: feature_type="gene"; breakpoint_role="nominal"; external_name="RNF212"; id="ENSG00000178222"; biotype="protein_coding"; position="4:1056247-1113697"
  - Used by: gene_region_annotation[1], verified_claims.C001
- **Source limitation:** Spatial overlap only: sv_type is retained for provenance but does not change this query. Nominal-interval and breakpoint-window results are reported separately; a parsed BND mate is also queried separately. Each scope first combines gene, regulatory, and repeat features; a failed combined request falls back to serialized per-feature queries. A heuristic breakpoint window retrieves nearby features but is not a measured confidence interval. Results are capped per feature type; transcript, consequence, breakpoint, nearest-gene, and mappability annotation are not included. A null feature list means that feature query failed.

### gnomAD-SV

- **GNO-BL-001** (partial_overlap): gnomAD-SV DEL_chr4_09a860e6 is a partial_overlap match (AF=0.577634).
  - Key facts: variant_id="DEL_chr4_09a860e6"; type="DEL"; af=0.577634; ac=72835; an=126092; match_metrics={"start_offset_bp": -1, "end_offset_bp": 0, "start_within_allowed_window": false, "end_within_allowed_window": true, "start_window_source": "heuristic_fallback", "end_window_source": "heuristic_fallback", "reciprocal_overlap_query": 1.0, "reciprocal_overlap_database": 0.980392, "size_similarity": 0.980392}; position="4:1092989-1093039"
  - Used by: population_evidence[1], verified_claims.C003
  - Source: https://gnomad.broadinstitute.org/variant/DEL_chr4_09a860e6?dataset=gnomad_sv_r4
- **Source limitation:** Similarity classes are deterministic screening labels, not proof of variant identity or biological effect. Heuristic windows are used only when VCF breakpoint confidence intervals are unavailable. BND records with a parsed mate are compared using both breakends and the chromosome pair, allowing reversed record order. Input orientation is retained but cannot be compared because it is absent from this gnomAD response. BND records without a mate retain first-breakend-only candidate matching. Adaptive retrieval padding, when nonzero, widens only the records retrieved from the API; it never widens the fixed matching windows. A gnomAD-SV absence does not establish novelty, pathogenicity, or technical validity.

### PubMed

- **PMID-22844258** (citation_found): Genetic variants in REC8, RNF212, and PRDM9 influence male recombination in cattle.
  - Key facts: authors=["Sandor C", "Li W", "Coppieters W"]; author_count=6; source="PLoS Genet"; pubdate="2012"; doi="10.1371/journal.pgen.1002854"
  - Used by: verified_claims.C004
  - Source: https://pubmed.ncbi.nlm.nih.gov/22844258/
- **PMID-24390283** (citation_found): Antagonistic roles of ubiquitin ligase HEI10 and SUMO ligase RNF212 regulate meiotic recombination.
  - Key facts: authors=["Qiao H", "Prasada Rao HB", "Yang Y"]; author_count=14; source="Nat Genet"; pubdate="2014 Feb"; doi="10.1038/ng.2858"
  - Used by: verified_claims.C004
  - Source: https://pubmed.ncbi.nlm.nih.gov/24390283/
- **PMID-27516620** (citation_found): Coding and noncoding variants in HFM1, MLH3, MSH4, MSH5, RNF212, and RNF212B affect recombination rate in cattle.
  - Key facts: authors=["Kadri NK", "Harland C", "Faux P"]; author_count=14; source="Genome Res"; pubdate="2016 Oct"; doi="10.1101/gr.204214.116"
  - Used by: verified_claims.C004
  - Source: https://pubmed.ncbi.nlm.nih.gov/27516620/
- **PMID-35596132** (citation_found): Recombination rates in pigs differ between breeds, sexes and individuals, and are associated with the RNF212, SYCP2, PRDM7, MEI1 and MSH4 loci.
  - Key facts: authors=["Brekke C", "Berg P", "Gjuvsland AB"]; author_count=4; source="Genet Sel Evol"; pubdate="2022 May 20"; doi="10.1186/s12711-022-00723-9"
  - Used by: verified_claims.C004
  - Source: https://pubmed.ncbi.nlm.nih.gov/35596132/
- **PMID-41565805** (citation_found): Common variation in meiosis genes shapes human recombination and aneuploidy.
  - Key facts: authors=["Carioscia SA", "Biddanda A", "Starostik MR"]; author_count=7; source="Nature"; pubdate="2026 Mar"; doi="10.1038/s41586-025-09964-2"
  - Used by: verified_claims.C004
  - Source: https://pubmed.ncbi.nlm.nih.gov/41565805/
- **Source limitation:** Metadata does not prove that the full text supports a biological claim.

### Artifact-risk rules

- **QC-BL-001** (unknown): low_call_rate: unknown. Missingness can produce spurious population differences.
  - Key facts: risk_type="low_call_rate"; recommended_check="Calculate call rate per cohort."
  - Used by: artifact_risks.low_call_rate
- **QC-BL-002** (unknown): single_caller_support: unknown. A call from one algorithm may reflect caller-specific bias.
  - Key facts: risk_type="single_caller_support"; recommended_check="Validate with an orthogonal caller or experimental assay."
  - Used by: artifact_risks.single_caller_support
- **QC-BL-003** (present): repeat_region: present. Repeats in breakpoint windows can make breakpoint placement unreliable.
  - Key facts: risk_type="repeat_region"; evidence={"scope": "breakpoint_windows", "start_repeat_count": 2, "end_repeat_count": 2}; recommended_check="Confirm both breakpoints against a curated repeat track."
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

- **VEP-BL-001** (modifier): VEP predicts intron_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000433731"; consequence_terms=["intron_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=true; mane_select="NM_001131034.4"
  - Used by: gene_region_annotation[1], gene_region_annotation[2], verified_claims.C001, verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-002** (modifier): VEP predicts intron_variant, non_coding_transcript_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000512552"; consequence_terms=["intron_variant", "non_coding_transcript_variant"]; impact="MODIFIER"; percentage_overlap=0.35; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-003** (modifier): VEP predicts intron_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000382968"; consequence_terms=["intron_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-004** (modifier): VEP predicts intron_variant, NMD_transcript_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000508428"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-005** (modifier): VEP predicts intron_variant, NMD_transcript_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000510715"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-006** (modifier): VEP predicts intron_variant, NMD_transcript_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000511620"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-007** (modifier): VEP predicts intron_variant, NMD_transcript_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000984828"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-008** (modifier): VEP predicts intron_variant, NMD_transcript_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00000984829"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-009** (modifier): VEP predicts intron_variant, NMD_transcript_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00001049740"; consequence_terms=["intron_variant", "NMD_transcript_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-010** (modifier): VEP predicts intron_variant for RNF212 (MODIFIER).
  - Key facts: gene_symbol="RNF212"; gene_id="ENSG00000178222"; transcript_id="ENST00001138440"; consequence_terms=["intron_variant"]; impact="MODIFIER"; percentage_overlap=0.12; canonical=false
  - Used by: gene_region_annotation[2], verified_claims.C002
  - Source: https://rest.ensembl.org/vep/human/region/4:1092990-1093039:1/DEL?canonical=1;mane=1;numbers=1
- **Source limitation:** VEP consequences are predictions for the submitted interval and symbolic allele. They do not establish expression change, dosage pathogenicity, phenotype, penetrance, or the actual transcript expressed in a sample. Only a ranked compact subset of consequences is retained.


## Query provenance

- Ensembl: found — {"query_region": "4:1092990-1093039", "query_strategy": "combined"}
- Ensembl VEP: found — {"query_region": "4:1092990-1093039"}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "4", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: not_found — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [1092490, 1093539]}], "query_strategy": "expanded_full_interval"}
- PubMed: not_found — "RNF212" AND "deletion" AND "intron"
- PubMed: found — "RNF212" AND "recombination"
