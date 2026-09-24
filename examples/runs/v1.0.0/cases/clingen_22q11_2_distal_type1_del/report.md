# Structural Variant Investigation Report

**Status:** incomplete

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

- Query budget used: 1/2
- Stop reason: No further whitelisted actions will materially resolve the remaining truncation limits or change the clinical interpretation of this well-characterized 22q11.2 recurrent distal microdeletion.
- QUERY_TRANSCRIPTS — executed: The baseline gene annotations (region_annotation['features']['gene']) and VEP consequences (vep_evidence['records']) are both truncated, leaving an incomplete profile of the protein-coding genes and transcripts fully or partially ablated in this 1.05 Mb deletion region.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The genomic region coordinates contain several annotated genes and transcripts, including non-coding RNA genes such as lncRNAs and miRNAs. (kind: database_fact; confidence: high; evidence: ENS-BL-NOMINAL-GENE-001, ENS-BL-NOMINAL-GENE-002, ENS-BL-NOMINAL-GENE-003, ENS-ADP-NOMINAL-TRANSCRIPT-001, ENS-ADP-NOMINAL-TRANSCRIPT-002, ENS-ADP-NOMINAL-TRANSCRIPT-003)
- Multiple regulatory features, including promoters and enhancers, are annotated within the deleted interval. (kind: database_fact; confidence: high; evidence: ENS-BL-NOMINAL-REGULATORY-001, ENS-BL-NOMINAL-REGULATORY-002, ENS-BL-NOMINAL-REGULATORY-003, ENS-BL-NOMINAL-REGULATORY-004, ENS-BL-NOMINAL-REGULATORY-005)

## Population and variant-database evidence

- Multiple partially overlapping deletion variants are recorded in gnomAD-SV at very low allele frequencies. (kind: database_fact; confidence: high; evidence: GNO-BL-001, GNO-BL-002, GNO-BL-003, GNO-BL-004, GNO-BL-005, GNO-BL-006, GNO-BL-007, GNO-BL-008, GNO-BL-009, GNO-BL-010)
- Overlapping copy number losses are observed in healthy control cohorts compiled in the DGV Gold Standard dataset. (kind: database_fact; confidence: high; evidence: DGV-BL-001, DGV-BL-002, DGV-BL-003, DGV-BL-004, DGV-BL-005, DGV-BL-006, DGV-BL-007, DGV-BL-008, DGV-BL-009, DGV-BL-010)
- Multiple small sequence-resolved copy number variants in dbVar overlap individual genes like MAPK1 or YPEL1 within this genomic region. (kind: database_fact; confidence: high; evidence: DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008, DBV-BL-009, DBV-BL-010)

## Clinical evidence and phenotype associations

- The 22q11.2 recurrent region (distal type I, D-E or D-F) has sufficient evidence for haploinsufficiency (score 3) based on expert ClinGen curation. (kind: database_fact; confidence: high; evidence: CGD-BL-001)
- The TOP3B gene has no evidence for haploinsufficiency (score 0) according to ClinGen expert curation. (kind: database_fact; confidence: high; evidence: CGD-BL-002)
- A partially overlapping deletion variant in ClinVar is classified as likely pathogenic for Schizophrenia. (kind: database_fact; confidence: high; evidence: CLV-BL-001)
- A partially overlapping deletion variant in ClinVar is classified as likely pathogenic for Autism. (kind: database_fact; confidence: high; evidence: CLV-BL-002)
- A partially overlapping copy number variation variant in dbVar is classified as of uncertain significance. (kind: database_fact; confidence: high; evidence: DBV-BL-001)

## Literature evidence

No evidence recorded.

## Possible interpretations

- The deletion is predicted by VEP to cause complete transcript ablation of multiple protein-coding genes, including MAPK1, TOP3B, and UBE2L3. (kind: inference; confidence: high; evidence: VEP-BL-001, VEP-BL-002, VEP-BL-003, VEP-BL-004, VEP-BL-005, VEP-BL-006, VEP-BL-007, VEP-BL-008, VEP-BL-009, VEP-BL-010)
- The high density of repeat sequences at both breakpoints presents a potential risk of low-accuracy alignment or breakpoint misplacement. (kind: inference; confidence: high; evidence: QC-BL-003)

## Qualified findings

- Repeat sequences, such as Alu elements and simple repeats, are annotated near both the start and end breakpoints of this genomic region. (evidence: ENS-BL-START-REPEAT-001, ENS-BL-START-REPEAT-002, ENS-BL-START-REPEAT-003, ENS-BL-END-REPEAT-001, ENS-BL-END-REPEAT-002, ENS-BL-END-REPEAT-003; qualification: Partially supported. While multiple Alu elements (AluY, AluSx1) and other repeat sequences (ERV3, MLT2C2) are annotated at both breakpoints, no 'simple repeats' are explicitly present in the referenced Ensembl repeat annotations.)
- Published clinical literature describes patients with distal 22q11.2 deletions presenting with phenotypes such as congenital heart defects, immunodeficiency, or craniofacial microsomia. (evidence: PMID-22318985, PMID-25123976, PMID-29288792, PMID-32256297, PMID-41165438; qualification: Supported by the provided PMIDs which map directly to distal deletions and these clinical phenotypes (e.g., PMID-22318985 for congenital heart defects, PMID-32256297 for immunodeficiency, and PMID-29288792 for craniofacial microsomia).; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- Published literature links deletion or loss of TOP3B with cognitive impairment, facial dysmorphism, autism susceptibility, or genome instability. (evidence: PMID-27880953, PMID-31795919, PMID-32028044; qualification: Supported by the referenced PMIDs associating TOP3B loss with cognitive impairment, facial dysmorphism, autism, and genomic instability.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- Scientific literature outlines functional roles of UBE2L3 in inflammation and its association with copy number variations. (evidence: PMID-37474493, PMID-37372436, PMID-10760570; qualification: Supported by literature abstracts linking UBE2L3 to IL-1beta/inflammation regulation and copy number variation studies.; Only PubMed citation metadata was retrieved; full-text support was not checked.)

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
- The retrieved DGV Gold Standard dataset represents healthy controls using historical cohorts and may suffer from boundary imprecision.
- PubMed findings represent association and annotation metadata and do not provide direct experimental proof of pathogenesis for this specific structural variant.
- gnomAD-SV dataset has filtering annotations (e.g., IGH_MHC_OVERLAP) that might suggest alignment complexity in overlapping regions.
- Conservatively qualified claim C012: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C013: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C014: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Ensembl query was incomplete (found).

## Recommended next steps

- Resolve evidence gap: Baseline gene annotations and VEP predicted consequences are truncated in the raw response, limiting complete characterization of all transcripts across the 1.05 Mb region.
- Resolve evidence gap: No experimental expression or patient-specific RNA-seq data is available within the collected evidence to confirm downstream impact on protein levels for ablated transcripts.

## Evidence catalog

- **CGD-BL-001** [ClinGen Dosage; exact]: ClinGen Dosage record ISCA-37397 — https://search.clinicalgenome.org/kb/gene-dosage/region/ISCA-37397
- **CGD-BL-002** [ClinGen Dosage; region_overlap]: ClinGen Dosage record HGNC:11993 — https://search.clinicalgenome.org/kb/gene-dosage/HGNC:11993
- **CLV-BL-001** [ClinVar; region_overlap]: NC_000022.11:g.(?_21956007)_(22224188_?)del — https://www.ncbi.nlm.nih.gov/clinvar/variation/545270/
- **CLV-BL-002** [ClinVar; region_overlap]: NC_000022.11:g.(?_21959229)_(22218520_?)del — https://www.ncbi.nlm.nih.gov/clinvar/variation/545271/
- **DBV-BL-001** [dbVar; partial_overlap]: dbVar record nsv7907941 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7907941/
- **DBV-BL-002** [dbVar; region_overlap]: dbVar record nsv7844015 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7844015/
- **DBV-BL-003** [dbVar; region_overlap]: dbVar record nsv7842013 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7842013/
- **DBV-BL-004** [dbVar; region_overlap]: dbVar record nsv7841961 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7841961/
- **DBV-BL-005** [dbVar; region_overlap]: dbVar record nsv7842069 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7842069/
- **DBV-BL-006** [dbVar; region_overlap]: dbVar record nsv7844947 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7844947/
- **DBV-BL-007** [dbVar; region_overlap]: dbVar record nsv7854090 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7854090/
- **DBV-BL-008** [dbVar; region_overlap]: dbVar record nsv7869251 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7869251/
- **DBV-BL-009** [dbVar; region_overlap]: dbVar record nsv7841714 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7841714/
- **DBV-BL-010** [dbVar; region_overlap]: dbVar record nsv7855412 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7855412/
- **DGV-BL-001** [DGV Gold; partial_overlap]: DGV Gold record gssvL76611 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=21960704;end=22916199
- **DGV-BL-002** [DGV Gold; region_overlap]: DGV Gold record gssvL76614 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=21943274;end=22245870
- **DGV-BL-003** [DGV Gold; region_overlap]: DGV Gold record gssvL76616 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=22315110;end=22604355
- **DGV-BL-004** [DGV Gold; region_overlap]: DGV Gold record gssvL76619 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=22099154;end=22340029
- **DGV-BL-005** [DGV Gold; region_overlap]: DGV Gold record gssvL76618 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=21955958;end=22168231
- **DGV-BL-006** [DGV Gold; region_overlap]: DGV Gold record gssvL76621 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=22039206;end=22207925
- **DGV-BL-007** [DGV Gold; region_overlap]: DGV Gold record gssvL76623 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=22228239;end=22331920
- **DGV-BL-008** [DGV Gold; region_overlap]: DGV Gold record gssvL76627 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=22162643;end=22247403
- **DGV-BL-009** [DGV Gold; region_overlap]: DGV Gold record gssvL76632 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=22086417;end=22168342
- **DGV-BL-010** [DGV Gold; region_overlap]: DGV Gold record gssvL76633 — https://api.genome.ucsc.edu/getData/track?genome=hg38;track=dgvGold;chrom=chr22;start=21960939;end=22027424
- **ENS-ADP-NOMINAL-TRANSCRIPT-001** [Ensembl; contextual]: Ensembl record ENST00000609038
- **ENS-ADP-NOMINAL-TRANSCRIPT-002** [Ensembl; contextual]: MIR301B-201
- **ENS-ADP-NOMINAL-TRANSCRIPT-003** [Ensembl; contextual]: MIR130B-201
- **ENS-BL-END-REPEAT-001** [Ensembl; region_overlap]: ERV3-16A3_I-int
- **ENS-BL-END-REPEAT-002** [Ensembl; region_overlap]: AluSx1
- **ENS-BL-END-REPEAT-003** [Ensembl; region_overlap]: MLT2C2
- **ENS-BL-NOMINAL-GENE-001** [Ensembl; region_overlap]: novel transcript
- **ENS-BL-NOMINAL-GENE-002** [Ensembl; region_overlap]: microRNA 301b [Source:HGNC Symbol;Acc:HGNC:33667]
- **ENS-BL-NOMINAL-GENE-003** [Ensembl; region_overlap]: microRNA 130b [Source:HGNC Symbol;Acc:HGNC:31515]
- **ENS-BL-NOMINAL-REGULATORY-001** [Ensembl; region_overlap]: promoter
- **ENS-BL-NOMINAL-REGULATORY-002** [Ensembl; region_overlap]: enhancer
- **ENS-BL-NOMINAL-REGULATORY-003** [Ensembl; region_overlap]: enhancer
- **ENS-BL-NOMINAL-REGULATORY-004** [Ensembl; region_overlap]: enhancer
- **ENS-BL-NOMINAL-REGULATORY-005** [Ensembl; region_overlap]: enhancer
- **ENS-BL-START-REPEAT-001** [Ensembl; region_overlap]: AluY
- **ENS-BL-START-REPEAT-002** [Ensembl; region_overlap]: AluY
- **ENS-BL-START-REPEAT-003** [Ensembl; region_overlap]: AluY
- **GNO-BL-001** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_393105dd?dataset=gnomad_sv_r4
- **GNO-BL-002** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_6e78a7ae?dataset=gnomad_sv_r4
- **GNO-BL-003** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_503eb8a7?dataset=gnomad_sv_r4
- **GNO-BL-004** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_15bd4ecb?dataset=gnomad_sv_r4
- **GNO-BL-005** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_9ca092b0?dataset=gnomad_sv_r4
- **GNO-BL-006** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_445d78e6?dataset=gnomad_sv_r4
- **GNO-BL-007** [gnomAD-SV; partial_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_38d70944?dataset=gnomad_sv_r4
- **GNO-BL-008** [gnomAD-SV; region_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_153c96e2?dataset=gnomad_sv_r4
- **GNO-BL-009** [gnomAD-SV; region_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_70b1a5e8?dataset=gnomad_sv_r4
- **GNO-BL-010** [gnomAD-SV; region_overlap]: Candidate similarity only; the available evidence does not establish that this is the same biological event. — https://gnomad.broadinstitute.org/variant/DEL_chr22_a1666a1d?dataset=gnomad_sv_r4
- **PMID-10760570** [PubMed; contextual]: Promoter analysis of the human ubiquitin-conjugating enzyme gene family UBE2L1-4, including UBE2L3 which encodes UbcH7. — https://pubmed.ncbi.nlm.nih.gov/10760570/
- **PMID-22318985** [PubMed; contextual]: Congenital heart defects in a novel recurrent 22q11.2 deletion harboring the genes CRKL and MAPK1. — https://pubmed.ncbi.nlm.nih.gov/22318985/
- **PMID-25123976** [PubMed; contextual]: Central 22q11.2 deletions. — https://pubmed.ncbi.nlm.nih.gov/25123976/
- **PMID-27880953** [PubMed; contextual]: Deletion of TOP3B Is Associated with Cognitive Impairment and Facial Dysmorphism. — https://pubmed.ncbi.nlm.nih.gov/27880953/
- **PMID-29288792** [PubMed; contextual]: Distal deletion at 22q11.2 as differential diagnosis in Craniofacial Microsomia: Case report and literature review. — https://pubmed.ncbi.nlm.nih.gov/29288792/
- **PMID-31795919** [PubMed; contextual]: Loss of TOP3B leads to increased R-loop formation and genome instability. — https://pubmed.ncbi.nlm.nih.gov/31795919/
- **PMID-32028044** [PubMed; contextual]: Further evidence of GABRA4 and TOP3B as autism susceptibility genes. — https://pubmed.ncbi.nlm.nih.gov/32028044/
- **PMID-32256297** [PubMed; contextual]: Immunodeficiency in a Patient with 22q11.2 Distal Deletion Syndrome and a p.Ala7dup Variant in the MAPK1 Gene. — https://pubmed.ncbi.nlm.nih.gov/32256297/
- **PMID-37372436** [PubMed; contextual]: Genomic Landscape of Copy Number Variations and Their Associations with Climatic Variables in the World's Sheep. — https://pubmed.ncbi.nlm.nih.gov/37372436/
- **PMID-37474493** [PubMed; contextual]: IL-1β turnover by the UBE2L3 ubiquitin conjugating enzyme and HECT E3 ligases limits inflammation. — https://pubmed.ncbi.nlm.nih.gov/37474493/
- **PMID-41165438** [PubMed; contextual]: Mexican Patients With Suspected 22q11.2 Deletion Syndrome: Clinical Characterization and Molecular Findings by Fluorescence In Situ Hybridization and Multiplex Ligation-Dependent Probe Amplification. — https://pubmed.ncbi.nlm.nih.gov/41165438/
- **QC-BL-001** [Artifact-risk rules; contextual]: low_call_rate
- **QC-BL-002** [Artifact-risk rules; contextual]: single_caller_support
- **QC-BL-003** [Artifact-risk rules; contextual]: repeat_region
- **QC-BL-004** [Artifact-risk rules; contextual]: low_mappability
- **QC-BL-005** [Artifact-risk rules; contextual]: supporting_reads
- **QC-BL-006** [Artifact-risk rules; contextual]: genotype_quality
- **QC-BL-007** [Artifact-risk rules; contextual]: batch_effect
- **VEP-BL-001** [Ensembl VEP; contextual]: MAPK1 — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-002** [Ensembl VEP; contextual]: SDF2L1 — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-003** [Ensembl VEP; contextual]: PPM1F — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-004** [Ensembl VEP; contextual]: YDJC — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-005** [Ensembl VEP; contextual]: CCDC116 — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-006** [Ensembl VEP; contextual]: ZNF280A — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-007** [Ensembl VEP; contextual]: YPEL1 — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-008** [Ensembl VEP; contextual]: UBE2L3 — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-009** [Ensembl VEP; contextual]: TOP3B — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1
- **VEP-BL-010** [Ensembl VEP; contextual]: PPIL2 — https://rest.ensembl.org/vep/human/region/22:21562828-22620608:1/DEL?canonical=1;mane=1;numbers=1

## Query provenance

- Ensembl: found — {"query_region": "22:21562828-22620608"}
- Ensembl VEP: found — {"query_region": "22:21562828-22620608"}
- gnomAD-SV: found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "22", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: found — {}
- ClinVar: found — {"query_regions": [{"role": "nominal", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [21562328, 22621108]}], "query_strategy": "expanded_full_interval"}
- PubMed: found — (TOP3B) AND deletion
- PubMed: found — (MAPK1) AND deletion AND (22q11.2)
- PubMed: found — (UBE2L3) AND deletion
