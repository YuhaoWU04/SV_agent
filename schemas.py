"""Pydantic schemas used at the structured-output boundaries."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ClaimType = Literal["observation", "database_fact", "inference", "hypothesis"]
Confidence = Literal["high", "medium", "low", "unknown"]
VerificationStatus = Literal[
    "supported", "partially_supported", "unsupported", "conflicting"
]


class VerifiedClaim(BaseModel):
    claim_id: str = Field(description="Stable identifier such as C001.")
    text: str
    claim_type: ClaimType
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Confidence
    verification_status: VerificationStatus
    notes: str = ""


class VerificationOutput(BaseModel):
    publication_allowed: bool = Field(
        description="True only when the report can be written without unsupported facts."
    )
    supported_claims: list[VerifiedClaim] = Field(default_factory=list)
    rejected_claims: list[VerifiedClaim] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SVSummary(BaseModel):
    validation_status: Literal["valid", "validation_error"] = "valid"
    sv_id: str = "unknown"
    genome_build: str | None = None
    genome_build_original: str | None = None
    chrom: str | None = None
    start: int | None = None
    end: int | None = None
    coordinate_system: Literal["1-based-inclusive"] = "1-based-inclusive"
    chromosome_length_bp: int | None = None
    sv_type: str | None = None
    sv_type_original: str | None = None
    sv_subtype: str | None = None
    length_bp: int | None = None


class ReportStatement(BaseModel):
    statement: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "unknown"
    kind: ClaimType = "observation"


class ArtifactRiskItem(BaseModel):
    risk_type: str
    status: Literal["present", "absent", "unknown"]
    impact: str
    evidence_ids: list[str] = Field(default_factory=list)
    recommended_check: str


class ProvenanceItem(BaseModel):
    source: str
    status: Literal["found", "not_found", "unavailable", "error", "not_queried"]
    query_summary: str
    retrieved_at: str = ""


class EvidenceRecord(BaseModel):
    evidence_id: str
    source: str
    status: Literal["found", "not_found", "unavailable", "error", "not_queried"]
    record_id: str = ""
    match_type: Literal[
        "exact", "region_search", "region_overlap", "nearby", "gene_level", "contextual", "not_applicable"
    ] = "contextual"
    support_direction: Literal["supports", "contradicts", "contextual"] = "contextual"
    summary: str
    source_url: str = ""
    retrieved_at: str = ""
    limitations: str = ""


class SVReport(BaseModel):
    report_version: str = "0.1"
    report_status: Literal["complete", "incomplete", "blocked"]
    sv_summary: SVSummary
    statistical_signals: list[ReportStatement] = Field(default_factory=list)
    gene_region_annotation: list[ReportStatement] = Field(default_factory=list)
    population_evidence: list[ReportStatement] = Field(default_factory=list)
    clinical_phenotype_evidence: list[ReportStatement] = Field(default_factory=list)
    literature_evidence: list[ReportStatement] = Field(default_factory=list)
    functional_evidence: list[ReportStatement] = Field(default_factory=list)
    artifact_risks: list[ArtifactRiskItem] = Field(default_factory=list)
    possible_interpretations: list[ReportStatement] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    verified_claims: list[VerifiedClaim] = Field(default_factory=list)
    evidence_catalog: list[EvidenceRecord] = Field(default_factory=list)
    query_provenance: list[ProvenanceItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_internal_links(self) -> "SVReport":
        if self.sv_summary.validation_status == "validation_error":
            if self.report_status != "blocked":
                raise ValueError("a validation_error input requires a blocked report")
        else:
            if self.sv_summary.genome_build not in {"GRCh37", "GRCh38"}:
                raise ValueError("a valid report requires GRCh37 or GRCh38")
            if self.sv_summary.sv_type not in {"DEL", "DUP", "INV", "INS", "BND", "CNV"}:
                raise ValueError("a valid report has an unsupported SV type")
            if self.sv_summary.start is None or self.sv_summary.end is None:
                raise ValueError("a valid report requires coordinates")

        catalog_ids = [item.evidence_id for item in self.evidence_catalog]
        if len(catalog_ids) != len(set(catalog_ids)):
            raise ValueError("evidence_catalog contains duplicate evidence IDs")
        known = set(catalog_ids)
        used: set[str] = set()
        statement_groups = (
            self.statistical_signals,
            self.gene_region_annotation,
            self.population_evidence,
            self.clinical_phenotype_evidence,
            self.literature_evidence,
            self.functional_evidence,
            self.possible_interpretations,
        )
        for group in statement_groups:
            for statement in group:
                used.update(statement.evidence_ids)
        for risk in self.artifact_risks:
            used.update(risk.evidence_ids)
        for claim in self.verified_claims:
            used.update(claim.evidence_ids)
        missing = used - known
        if missing:
            raise ValueError(f"unknown evidence IDs referenced: {sorted(missing)}")
        return self
