"""Google ADK SequentialAgent definition for candidate-SV investigation."""

from __future__ import annotations

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext

from .config import MODEL
from .prompts import ADAPTIVE, BASELINE, INTAKE, LITERATURE, REPORT, VERIFY
from .schemas import SVReport, VerificationOutput
from .tools import (
    collect_baseline_evidence,
    normalize_sv_input,
    run_budgeted_adaptive_action,
    search_pubmed,
)


def adaptive_followup_query(
    normalized_sv_json: str,
    action: str,
    evidence_gap: str,
    reason: str,
    expected_information_gain: str,
    tool_context: ToolContext,
) -> dict:
    """Run one budgeted, audited follow-up from the fixed action whitelist.

    Args:
        normalized_sv_json: The complete JSON emitted by InputNormalizerAgent.
        action: One exact action name listed in the adaptive-agent instruction.
        evidence_gap: Specific unresolved question in the baseline evidence.
        reason: Why this action is appropriate for that gap.
        expected_information_gain: How the result could change interpretation.
        tool_context: Injected ADK context; never supplied by the model.
    """
    return run_budgeted_adaptive_action(
        normalized_sv_json=normalized_sv_json,
        action=action,
        evidence_gap=evidence_gap,
        reason=reason,
        expected_information_gain=expected_information_gain,
        state=tool_context.state,
    )


input_normalizer_agent = Agent(
    name="InputNormalizerAgent",
    model=MODEL,
    description="Validates and normalizes one candidate SV without inference.",
    instruction=INTAKE,
    tools=[normalize_sv_input],
    output_key="normalized_sv",
)

baseline_evidence_agent = Agent(
    name="BaselineEvidenceCollectorAgent",
    model=MODEL,
    description="Runs the required deterministic Ensembl, gnomAD-SV, and QC baseline.",
    instruction=BASELINE,
    tools=[collect_baseline_evidence],
    output_key="baseline_evidence",
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
    tools=[search_pubmed],
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
