"""Pydantic schemas used at the structured-output boundaries."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ClaimType = Literal["observation", "database_fact", "inference", "hypothesis"]
Confidence = Literal["high", "medium", "low", "unknown"]
VerificationStatus = Literal[
    "supported", "partially_supported", "unsupported", "conflicting"
]
ReportSection = Literal[
    "gene_region_annotation",
    "population_evidence",
    "clinical_phenotype_evidence",
    "literature_evidence",
    "possible_interpretations",
]


class VerifiedClaim(BaseModel):
    claim_id: str = Field(description="Stable identifier such as C001.")
    text: str
    claim_type: ClaimType
    report_section: ReportSection
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: Confidence
    verification_status: VerificationStatus
    notes: str = ""


class CandidateClaim(BaseModel):
    claim_id: str = Field(description="Stable identifier such as C001.")
    text: str = Field(description="One atomic claim, not a compound conclusion.")
    claim_type: ClaimType
    report_section: ReportSection = Field(
        description="Final report section for this claim if verification supports it."
    )
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_basis: str = Field(
        default="",
        description="Brief explanation of what the cited records directly establish.",
    )


class SynthesisOutput(BaseModel):
    candidate_claims: list[CandidateClaim] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def clean_candidate_claims(self) -> "SynthesisOutput":
        dropped = [
            claim.claim_id
            for claim in self.candidate_claims
            if claim.claim_type in {"observation", "database_fact"}
            and not claim.evidence_ids
        ]
        if dropped:
            self.candidate_claims = [
                claim for claim in self.candidate_claims if claim.claim_id not in dropped
            ]
            self.limitations.append(
                "Dropped factual candidate claims without evidence IDs: "
                + ", ".join(dropped)
            )
        claim_ids = [claim.claim_id for claim in self.candidate_claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("candidate claim IDs must be unique")
        return self


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
    cipos: list[int] | None = None
    ciend: list[int] | None = None
    start_confidence_interval: list[int] | None = None
    end_confidence_interval: list[int] | None = None
    breakpoint_uncertainty_status: Literal["complete", "partial", "not_provided"] = (
        "not_provided"
    )
    imprecise: bool = False
    bnd_mate_status: Literal[
        "coordinates_provided", "not_provided", "not_applicable"
    ] = "not_applicable"
    mate_chrom: str | None = None
    mate_pos: int | None = None
    mate_confidence_interval: list[int] | None = None
    local_orientation: Literal["+", "-"] | None = None
    mate_orientation: Literal["+", "-"] | None = None
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
    status: Literal[
        "found", "not_found", "not_applicable", "unavailable", "error",
        "not_queried",
    ]
    query_summary: str
    retrieved_at: str = ""


class EvidenceRecord(BaseModel):
    evidence_id: str
    source: str
    status: Literal[
        "found", "not_found", "not_applicable", "unavailable", "error",
        "not_queried",
    ]
    record_id: str = ""
    match_type: Literal[
        "exact", "high_similarity", "partial_overlap", "region_search",
        "region_overlap", "nearby", "gene_level", "contextual", "not_applicable"
    ] = "contextual"
    support_direction: Literal["supports", "contradicts", "contextual"] = "contextual"
    summary: str
    source_url: str = ""
    retrieved_at: str = ""
    limitations: str = ""


class InvestigationAction(BaseModel):
    action: str
    evidence_gap: str = ""
    reason: str = ""
    expected_information_gain: str = ""
    status: Literal["planned", "executed", "rejected", "not_executed"]
    result_status: str = ""
    rejection_reason: str = ""


class InvestigationLog(BaseModel):
    identified_evidence_gaps: list[str] = Field(default_factory=list)
    planned_actions: list[InvestigationAction] = Field(default_factory=list)
    executed_actions: list[InvestigationAction] = Field(default_factory=list)
    # Google GenAI's response-schema converter only accepts string-valued
    # ``Literal`` members. Equal min/max bounds preserve the fixed value while
    # remaining compatible with structured output generation.
    query_budget: int = Field(default=2, ge=2, le=2)
    queries_used: int = 0
    stop_reason: str
    remaining_limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def derive_budget_counts(cls, data: object) -> object:
        """Derive deterministic budget fields instead of trusting model copies."""
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        actions = normalized.get("executed_actions")
        if not isinstance(actions, list):
            actions = []
        normalized["query_budget"] = 2
        normalized["queries_used"] = sum(
            (
                action.get("status")
                if isinstance(action, dict)
                else getattr(action, "status", None)
            )
            == "executed"
            for action in actions
        )
        return normalized

    @model_validator(mode="after")
    def validate_budget(self) -> "InvestigationLog":
        if not 0 <= self.queries_used <= self.query_budget <= 2:
            raise ValueError("adaptive investigation query budget is invalid")
        # Rejected tool calls are retained in executed_actions for audit but do not
        # consume query budget. Only calls that reached an external adapter count.
        completed_calls = sum(
            action.status == "executed" for action in self.executed_actions
        )
        if completed_calls != self.queries_used:
            raise ValueError("executed action count does not match queries_used")
        return self


class SVReport(BaseModel):
    report_version: str = "1.0.0"
    report_status: Literal["complete", "incomplete", "blocked"]
    sv_summary: SVSummary
    statistical_signals: list[ReportStatement] = Field(default_factory=list)
    gene_region_annotation: list[ReportStatement] = Field(default_factory=list)
    population_evidence: list[ReportStatement] = Field(default_factory=list)
    clinical_phenotype_evidence: list[ReportStatement] = Field(default_factory=list)
    literature_evidence: list[ReportStatement] = Field(default_factory=list)
    artifact_risks: list[ArtifactRiskItem] = Field(default_factory=list)
    possible_interpretations: list[ReportStatement] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    verified_claims: list[VerifiedClaim] = Field(default_factory=list)
    evidence_catalog: list[EvidenceRecord] = Field(default_factory=list)
    query_provenance: list[ProvenanceItem] = Field(default_factory=list)
    investigation_log: InvestigationLog

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
            if not 1 <= self.sv_summary.start <= self.sv_summary.end:
                raise ValueError("valid report coordinates must be 1-based and ordered")
            if (
                self.sv_summary.chromosome_length_bp is not None
                and self.sv_summary.end > self.sv_summary.chromosome_length_bp
            ):
                raise ValueError("valid report coordinates exceed chromosome length")

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
