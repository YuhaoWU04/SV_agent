"""Google ADK SequentialAgent definition for candidate-SV investigation."""

from __future__ import annotations

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext

from .config import MAX_PUBMED_RECORDS, MODEL
from .prompts import ADAPTIVE, BASELINE, INTAKE, LITERATURE, REPORT, VERIFY
from .schemas import SVReport, VerificationOutput
from .state_pipeline import (
    adaptive_and_store,
    baseline_and_store,
    literature_and_store,
    normalize_and_store,
)


def normalize_sv_input_to_state(raw_input: str, tool_context: ToolContext) -> dict:
    """Normalize the complete user input and save the unmodified tool result.

    Args:
        raw_input: Complete candidate-SV JSON supplied by the user.
    """
    return normalize_and_store(raw_input, tool_context.state)


def collect_baseline_evidence_to_state(tool_context: ToolContext) -> dict:
    """Collect the required baseline from the candidate saved in session state.
    """
    return baseline_and_store(tool_context.state)


def adaptive_followup_query(
    action: str,
    evidence_gap: str,
    reason: str,
    expected_information_gain: str,
    tool_context: ToolContext,
) -> dict:
    """Run one budgeted, audited follow-up from the fixed action whitelist.

    Args:
        action: One exact action name listed in the adaptive-agent instruction.
        evidence_gap: Specific unresolved question in the baseline evidence.
        reason: Why this action is appropriate for that gap.
        expected_information_gain: How the result could change interpretation.
    """
    return adaptive_and_store(
        action=action,
        evidence_gap=evidence_gap,
        reason=reason,
        expected_information_gain=expected_information_gain,
        state=tool_context.state,
    )


def search_pubmed_to_state(
    query: str,
    tool_context: ToolContext,
    max_records: int = MAX_PUBMED_RECORDS,
) -> dict:
    """Search PubMed and save the complete metadata with stable evidence IDs.

    Args:
        query: A traceable PubMed query using coordinates, genes, or SV terms.
        max_records: Maximum citation summaries to return.
    """
    return literature_and_store(query, max_records, tool_context.state)


input_normalizer_agent = Agent(
    name="InputNormalizerAgent",
    model=MODEL,
    description="Validates and normalizes one candidate SV without inference.",
    instruction=INTAKE,
    tools=[normalize_sv_input_to_state],
)

baseline_evidence_agent = Agent(
    name="BaselineEvidenceCollectorAgent",
    model=MODEL,
    description=(
        "Runs the required deterministic Ensembl, gnomAD-SV, ClinGen, ClinVar, "
        "DGV, and QC baseline."
    ),
    instruction=BASELINE,
    tools=[collect_baseline_evidence_to_state],
)

adaptive_investigation_agent = Agent(
    name="AdaptiveInvestigationAgent",
    model=MODEL,
    description="Chooses at most two justified follow-ups from a fixed whitelist.",
    instruction=ADAPTIVE,
    tools=[adaptive_followup_query],
    output_key="adaptive_investigation",
)

literature_function_agent = Agent(
    name="LiteratureAndFunctionAgent",
    model=MODEL,
    description="Runs traceable, evidence-guided PubMed searches.",
    instruction=LITERATURE,
    tools=[search_pubmed_to_state],
    output_key="literature_evidence",
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
    description="Runs a fixed baseline plus a bounded, auditable adaptive investigation.",
    sub_agents=[
        input_normalizer_agent,
        baseline_evidence_agent,
        adaptive_investigation_agent,
        literature_function_agent,
        evidence_verifier_agent,
        report_writer_agent,
    ],
)
