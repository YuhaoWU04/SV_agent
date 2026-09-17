"""Google ADK SequentialAgent definition for candidate-SV investigation."""

from __future__ import annotations

from google.adk.agents import Agent, SequentialAgent

from .config import MODEL
from .prompts import ARTIFACT, DATABASE, INTAKE, LITERATURE, REGION, REPORT, VERIFY
from .schemas import SVReport, VerificationOutput
from .tools import (
    assess_artifact_risk,
    normalize_sv_input,
    query_ensembl_region,
    query_gnomad_sv,
    search_pubmed,
)


input_normalizer_agent = Agent(
    name="InputNormalizerAgent",
    model=MODEL,
    description="Validates and normalizes one candidate SV without inference.",
    instruction=INTAKE,
    tools=[normalize_sv_input],
    output_key="normalized_sv",
)

region_annotation_agent = Agent(
    name="RegionAnnotationAgent",
    model=MODEL,
    description="Collects coordinate-matched Ensembl region annotations.",
    instruction=REGION,
    tools=[query_ensembl_region],
    output_key="region_annotation",
)

database_evidence_agent = Agent(
    name="DatabaseEvidenceAgent",
    model=MODEL,
    description="Collects and classifies build-matched gnomAD-SV population evidence.",
    instruction=DATABASE,
    tools=[query_gnomad_sv],
    output_key="database_evidence",
)

literature_function_agent = Agent(
    name="LiteratureAndFunctionAgent",
    model=MODEL,
    description="Runs traceable literature searches without inferring from titles.",
    instruction=LITERATURE,
    tools=[search_pubmed],
    output_key="literature_evidence",
)

artifact_risk_agent = Agent(
    name="ArtifactRiskAgent",
    model=MODEL,
    description="Assesses missingness, repeat, caller, and batch-related risks.",
    instruction=ARTIFACT,
    tools=[assess_artifact_risk],
    output_key="artifact_risk",
)

# Structured-output agents deliberately have no tools. ADK warns that combining
# tools and output_schema is model-dependent; the split keeps the boundary stable.
evidence_verifier_agent = Agent(
    name="EvidenceVerifierAgent",
    model=MODEL,
    description="Performs claim-level grounding and overinterpretation checks.",
    instruction=VERIFY,
    output_schema=VerificationOutput,
    output_key="verification",
)

report_writer_agent = Agent(
    name="ReportWriterAgent",
    model=MODEL,
    description="Produces the final machine-readable, evidence-linked SV report.",
    instruction=REPORT,
    output_schema=SVReport,
    output_key="final_report",
)

root_agent = SequentialAgent(
    name="SVInvestigationPipeline",
    description="Investigates one pre-screened SV in a fixed, auditable sequence.",
    sub_agents=[
        input_normalizer_agent,
        region_annotation_agent,
        database_evidence_agent,
        literature_function_agent,
        artifact_risk_agent,
        evidence_verifier_agent,
        report_writer_agent,
    ],
)
