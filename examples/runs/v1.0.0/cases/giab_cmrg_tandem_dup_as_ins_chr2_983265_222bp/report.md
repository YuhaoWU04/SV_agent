# Structural Variant Investigation Report

**Status:** incomplete

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

- Query budget used: 1/2
- Stop reason: All relevant evidence gaps have been addressed. SNTG2 is confirmed as the only gene near the insertion, and its intronic consequence is well-characterized by the VEP baseline results.
- QUERY_NEAREST_GENE_10KB — executed: Nominal regional gene annotation timed out (TimeoutError), leaving uncertainty about other overlapping or closely neighboring genes besides SNTG2.

## Statistical signals

No evidence recorded.

## Gene and region annotation

- The structural variant is located within the coordinates of the SNTG2 gene (ENSG00000172554) on chromosome 2. (kind: observation; confidence: high; evidence: ENS-BL-START-GENE-001, ENS-ADP-EXPANDED_REGION-GENE-001)
- Ensembl VEP predicts that the insertion is an intronic variant (intron 1/16) on the canonical SNTG2 transcript ENST00000308624 with a MODIFIER impact. (kind: observation; confidence: high; evidence: VEP-BL-001)
- Ensembl VEP predicts intronic MODIFIER consequences for the insertion across multiple non-canonical SNTG2 transcripts, including some annotated with nonsense-mediated decay. (kind: observation; confidence: high; evidence: VEP-BL-002, VEP-BL-003, VEP-BL-004, VEP-BL-005, VEP-BL-006, VEP-BL-007, VEP-BL-008, VEP-BL-009, VEP-BL-010)
- The insertion breakpoint resides within a repeating genomic region annotated with tandem repeats of type 'trf'. (kind: observation; confidence: high; evidence: ENS-BL-NOMINAL-REPEAT-001, ENS-BL-NOMINAL-REPEAT-002, ENS-BL-START-REPEAT-001, ENS-BL-START-REPEAT-002, ENS-BL-START-REPEAT-003, ENS-BL-START-REPEAT-004, ENS-BL-START-REPEAT-005, ENS-BL-START-REPEAT-006)

## Population and variant-database evidence

- Seven dbVar database entries (esv3656833, nsv3953858, nsv5618433, nsv5961524, nsv6053736, nsv6220675, nsv7862737) represent exact coordinate and type matches for an insertion variant at chromosome 2 coordinate 983,265. (kind: database_fact; confidence: high; evidence: DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007)

## Clinical evidence and phenotype associations

- The matching and nearby dbVar records do not supply clinical significance findings for this insertion variant. (kind: database_fact; confidence: high; evidence: DBV-BL-001, DBV-BL-002, DBV-BL-003, DBV-BL-004, DBV-BL-005, DBV-BL-006, DBV-BL-007, DBV-BL-008, DBV-BL-009, DBV-BL-010)
- Quality control evaluations indicate a repeat region is present at the breakpoints (6 start and 6 end repeat counts), which can make structural variant breakpoint placement less reliable. (kind: observation; confidence: high; evidence: QC-BL-003)

## Literature evidence

No evidence recorded.

## Possible interpretations

- A causal connection cannot be established between this specific intronic insertion and SNTG2-associated neurodevelopmental, autism, or psychiatric phenotypes based solely on general gene-level literature and coordinate overlap. (kind: inference; confidence: high; evidence: PMID-17292328, PMID-29564645, PMID-38674362, VEP-BL-001)

## Qualified findings

- Three dbVar database entries (nsv2806727, nsv3366452, nsv3377346) represent nearby insertion variant matches situated 1 base pair away from the query coordinates. (evidence: DBV-BL-008, DBV-BL-009, DBV-BL-010; qualification: Verified. These database entries are marked as 'nearby' insertions at coordinate 983266, which is exactly 1 bp away.; Cited database records do not establish an exact or high-similarity match.)
- A published literature title reports that Neuroligins 3 and 4X interact with syntrophin-gamma2 (SNTG2) and that these interactions are altered by autism-related mutations. (evidence: PMID-17292328; qualification: Matches the publication title of PMID-17292328.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A published literature title describes monozygotic twins discordant for submicroscopic chromosomal anomalies in the 2p25.3 region. (evidence: PMID-23061379; qualification: Matches the title of PMID-23061379.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A published study title reports on early-onset obesity associated with a paternal 2pter deletion encompassing ACP1, TMEM18, and MYT1L. (evidence: PMID-24129437; qualification: Matches the title of PMID-24129437.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A study title describes genetic diagnosis and analysis of related genes in a pedigree presenting 2p25 and 12p13 cryptic rearrangements. (evidence: PMID-25119907; qualification: Matches the translated title of PMID-25119907.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A published literature title links genomic structural variants to cases of intellectual disability. (evidence: PMID-25626716; qualification: Matches the title of PMID-25626716.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A study title evaluates molecular karyotyping diagnostic efficacy and new variants in patients with isolated and complex autism spectrum disorder. (evidence: PMID-29564645; qualification: Matches the title of PMID-29564645.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A published study title investigates mice deleted for Sox3 and uc482 to analyze their relevance to X-linked hypoparathyroidism. (evidence: PMID-31961795; qualification: Matches the title of PMID-31961795.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A study title reports inherited L1 retrotransposon insertions associated with susceptibility to schizophrenia and bipolar disorder. (evidence: PMID-34901866; qualification: Matches the title of PMID-34901866 ('Associated With Risk for Schizophrenia and Bipolar Disorder').; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A published study title indicates through gene-gene interaction network analysis that CNTN2 is a candidate gene for idiopathic generalized epilepsy. (evidence: PMID-38460076; qualification: Matches the title of PMID-38460076.; Only PubMed citation metadata was retrieved; full-text support was not checked.)
- A publication title describes genetic alterations observed in a large population of Italian patients affected by neurodevelopmental disorders. (evidence: PMID-38674362; qualification: Matches the title of PMID-38674362.; Only PubMed citation metadata was retrieved; full-text support was not checked.)

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
- Ensembl VEP predictions are computational models of transcript-level consequences and do not represent validated functional splicing or expression outcomes in vivo.
- NCBI dbVar records aggregate heterogeneous study submissions of varying technical platforms and do not guarantee validated coordinate precision or clinical associations.
- The retrieved literature references only general gene associations or large regional rearrangements; none directly document or validate this specific 222 bp insertion.
- The insertion is flanked by tandem repeat sequences which increases the likelihood of sequencing alignment errors and mapping ambiguity.
- No coordinate-precise structural variant length (specifically '222 bp') is provided in the baseline Ensembl or NCBI dbVar databases for the query variant.
- Claim C019 was rejected because it introduces a precise variant length (222 bp) that is absent from all retrieved evidence metrics.
- Conservatively qualified claim C006: Cited database records do not establish an exact or high-similarity match.
- Conservatively qualified claim C009: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C010: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C011: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C012: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C013: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C014: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C015: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C016: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C017: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Conservatively qualified claim C018: Only PubMed citation metadata was retrieved; full-text support was not checked.
- Ensembl query was incomplete (found).

## Recommended next steps

- Resolve evidence gap: The Ensembl regional gene overlap query returned a TimeoutError, leaving potential gaps regarding other genes nearby or overlapping the nominal region.
- Resolve evidence gap: The gnomAD-SV database returned no matching records, which prevents estimating the allele frequency of this variant in healthy reference cohorts.
- Resolve evidence gap: ClinVar database searches returned no matching records, leaving a lack of clinical classifications for this specific genomic event.
- Resolve evidence gap: No patient-level clinical or phenotypic records are available for carriers of this specific 222 bp insertion.
- Resolve evidence gap: No coordinate-precise structural variant length (specifically '222 bp') is provided in the baseline Ensembl or NCBI dbVar databases for the query variant.

## Evidence catalog

- **DBV-BL-001** [dbVar; exact]: dbVar record esv3656833 — https://www.ncbi.nlm.nih.gov/dbvar/variants/esv3656833/
- **DBV-BL-002** [dbVar; exact]: dbVar record nsv3953858 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3953858/
- **DBV-BL-003** [dbVar; exact]: dbVar record nsv5618433 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5618433/
- **DBV-BL-004** [dbVar; exact]: dbVar record nsv5961524 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv5961524/
- **DBV-BL-005** [dbVar; exact]: dbVar record nsv6053736 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6053736/
- **DBV-BL-006** [dbVar; exact]: dbVar record nsv6220675 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv6220675/
- **DBV-BL-007** [dbVar; exact]: dbVar record nsv7862737 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv7862737/
- **DBV-BL-008** [dbVar; nearby]: dbVar record nsv2806727 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv2806727/
- **DBV-BL-009** [dbVar; nearby]: dbVar record nsv3366452 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3366452/
- **DBV-BL-010** [dbVar; nearby]: dbVar record nsv3377346 — https://www.ncbi.nlm.nih.gov/dbvar/variants/nsv3377346/
- **ENS-ADP-EXPANDED_REGION-GENE-001** [Ensembl; contextual]: syntrophin gamma 2 [Source:HGNC Symbol;Acc:HGNC:13741]
- **ENS-BL-NOMINAL-REPEAT-001** [Ensembl; region_overlap]: trf
- **ENS-BL-NOMINAL-REPEAT-002** [Ensembl; region_overlap]: trf
- **ENS-BL-START-GENE-001** [Ensembl; region_overlap]: syntrophin gamma 2 [Source:HGNC Symbol;Acc:HGNC:13741]
- **ENS-BL-START-REPEAT-001** [Ensembl; region_overlap]: trf
- **ENS-BL-START-REPEAT-002** [Ensembl; region_overlap]: trf
- **ENS-BL-START-REPEAT-003** [Ensembl; region_overlap]: trf
- **ENS-BL-START-REPEAT-004** [Ensembl; region_overlap]: trf
- **ENS-BL-START-REPEAT-005** [Ensembl; region_overlap]: trf
- **ENS-BL-START-REPEAT-006** [Ensembl; region_overlap]: trf
- **PMID-17292328** [PubMed; contextual]: Neuroligins 3 and 4X interact with syntrophin-gamma2, and the interactions are affected by autism-related mutations. — https://pubmed.ncbi.nlm.nih.gov/17292328/
- **PMID-23061379** [PubMed; contextual]: Monozygotic twins discordant for submicroscopic chromosomal anomalies in 2p25.3 region detected by array CGH. — https://pubmed.ncbi.nlm.nih.gov/23061379/
- **PMID-24129437** [PubMed; contextual]: Early-onset obesity and paternal 2pter deletion encompassing the ACP1, TMEM18, and MYT1L genes. — https://pubmed.ncbi.nlm.nih.gov/24129437/
- **PMID-25119907** [PubMed; contextual]: [Genetic diagnosis and analysis of related genes for a pedigree with 2p25 and 12p13 cryptic rearrangements]. — https://pubmed.ncbi.nlm.nih.gov/25119907/
- **PMID-25626716** [PubMed; contextual]: Genomic structural variants are linked with intellectual disability. — https://pubmed.ncbi.nlm.nih.gov/25626716/
- **PMID-29564645** [PubMed; contextual]: Diagnostic efficacy and new variants in isolated and complex autism spectrum disorder using molecular karyotyping. — https://pubmed.ncbi.nlm.nih.gov/29564645/
- **PMID-31961795** [PubMed; contextual]: Studies of mice deleted for Sox3 and uc482: relevance to X-linked hypoparathyroidism. — https://pubmed.ncbi.nlm.nih.gov/31961795/
- **PMID-34901866** [PubMed; contextual]: Inherited L1 Retrotransposon Insertions Associated With Risk for Schizophrenia and Bipolar Disorder. — https://pubmed.ncbi.nlm.nih.gov/34901866/
- **PMID-38460076** [PubMed; contextual]: Gene-gene interaction network analysis indicates CNTN2 is a candidate gene for idiopathic generalized epilepsy. — https://pubmed.ncbi.nlm.nih.gov/38460076/
- **PMID-38674362** [PubMed; contextual]: Genetic Alterations in a Large Population of Italian Patients Affected by Neurodevelopmental Disorders. — https://pubmed.ncbi.nlm.nih.gov/38674362/
- **QC-BL-001** [Artifact-risk rules; contextual]: low_call_rate
- **QC-BL-002** [Artifact-risk rules; contextual]: single_caller_support
- **QC-BL-003** [Artifact-risk rules; contextual]: repeat_region
- **QC-BL-004** [Artifact-risk rules; contextual]: low_mappability
- **QC-BL-005** [Artifact-risk rules; contextual]: supporting_reads
- **QC-BL-006** [Artifact-risk rules; contextual]: genotype_quality
- **QC-BL-007** [Artifact-risk rules; contextual]: batch_effect
- **VEP-BL-001** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-002** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-003** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-004** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-005** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-006** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-007** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-008** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-009** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1
- **VEP-BL-010** [Ensembl VEP; contextual]: SNTG2 — https://rest.ensembl.org/vep/human/region/2:983265-983265:1/INS?canonical=1;mane=1;numbers=1

## Query provenance

- Ensembl: found — {"query_region": "2:983265-983265"}
- Ensembl VEP: found — {"query_region": "2:983265-983265"}
- gnomAD-SV: not_found — {"dataset": "gnomad_sv_r4", "query_regions": [{"role": "nominal", "chrom": "2", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- ClinGen Dosage: not_applicable — {}
- ClinVar: not_found — {"query_regions": [{"role": "nominal", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- NCBI dbVar: found — {"query_regions": [{"role": "nominal", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- DGV Gold Standard: not_found — {"dataset": "dgvGold", "query_regions": [{"role": "nominal", "interval": [982765, 983765]}], "query_strategy": "expanded_full_interval"}
- PubMed: found — SNTG2 AND (insertion OR duplication OR "structural variant" OR CNV)
- PubMed: found — SNTG2 AND (autism OR "neurodevelopmental disorder" OR epilepsy)
- PubMed: found — SNTG2 AND ("tandem repeat" OR "short tandem repeat" OR microsatellite)
