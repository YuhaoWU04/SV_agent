"""Google ADK SequentialAgent definition for candidate-SV investigation."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from google.adk.agents import Agent, BaseAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.models import LlmResponse
from google.adk.tools import ToolContext
from google.genai import types

from .config import MAX_PUBMED_RECORDS, MODEL
from .prompts import ADAPTIVE, BASELINE, INTAKE, LITERATURE, SYNTHESIS, VERIFY
from .schemas import SVReport, SynthesisOutput, VerificationOutput
from .state_pipeline import (
    adaptive_and_store,
    baseline_and_store,
    build_evidence_view,
    finalize_report_from_state,
    literature_and_store,
    normalize_and_store,
    reconcile_verification_from_state,
)


def prepare_evidence_view(callback_context: CallbackContext) -> None:
    """Expose one deterministic ID-to-record projection to all later agents."""
    callback_context.state["evidence_view"] = build_evidence_view(
        callback_context.state
    )


def narrow_evidence_view(callback_context: CallbackContext) -> None:
    """Give verification only records cited by candidate claims."""
    synthesis = callback_context.state.get("claim_synthesis")
    claims = synthesis.get("candidate_claims", []) if isinstance(synthesis, dict) else []
    cited_ids = {
        evidence_id
        for claim in claims
        if isinstance(claim, dict)
        for evidence_id in claim.get("evidence_ids", [])
        if isinstance(evidence_id, str)
    }
    callback_context.state["evidence_view"] = build_evidence_view(
        callback_context.state, cited_ids
    )


def bind_verification_to_synthesis(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    """Prevent the verifier from adding or rewriting synthesis claims."""
    if not llm_response.content or not llm_response.content.parts:
        return None
    for index, part in enumerate(llm_response.content.parts):
        if not part.text:
            continue
        try:
            draft = json.loads(part.text)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(draft, dict):
            return None
        altered = llm_response.model_copy(deep=True)
        altered.content.parts[index].text = json.dumps(
            reconcile_verification_from_state(draft, callback_context.state),
            ensure_ascii=False,
        )
        return altered
    return None


class ReportAssemblyAgent(BaseAgent):
    """Deterministically assemble and emit the final validated report."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        report = SVReport.model_validate(
            finalize_report_from_state({}, ctx.session.state)
        ).model_dump(mode="json")
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=json.dumps(report, ensure_ascii=False))],
            ),
            actions=EventActions(state_delta={"final_report": report}),
        )


def normalize_sv_input_to_state(raw_input: str, tool_context: ToolContext) -> dict:
    """Normalize the complete user input and save the unmodified tool result.

    Args:
        raw_input: Complete candidate-SV JSON supplied by the user.
    """
    return normalize_and_store(raw_input, tool_context.state)


def collect_baseline_evidence_to_state(tool_context: ToolContext) -> dict:
    """Collect the required baseline from the candidate saved in session state."""
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
        "Runs the required deterministic Ensembl overlap/VEP, gnomAD-SV, ClinGen, "
        "ClinVar, dbVar, DGV, and QC baseline."
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

literature_agent = Agent(
    name="LiteratureAgent",
    model=MODEL,
    description="Runs traceable, evidence-guided PubMed searches.",
    instruction=LITERATURE,
    tools=[search_pubmed_to_state],
    output_key="literature_evidence",
)

# Structured-output agents deliberately have no tools. The synthesis callback builds
# their compact input from tool-owned state before ADK expands the instruction.
evidence_synthesis_agent = Agent(
    name="EvidenceSynthesisAgent",
    model=MODEL,
    description="Converts collected evidence into atomic candidate claims.",
    instruction=SYNTHESIS,
    output_schema=SynthesisOutput,
    output_key="claim_synthesis",
    before_agent_callback=prepare_evidence_view,
    include_contents="none",
)

evidence_verifier_agent = Agent(
    name="EvidenceVerifierAgent",
    model=MODEL,
    description="Performs claim-level grounding and overinterpretation checks.",
    instruction=VERIFY,
    output_schema=VerificationOutput,
    output_key="verification",
    before_agent_callback=narrow_evidence_view,
    after_model_callback=bind_verification_to_synthesis,
    include_contents="none",
)

report_assembly_agent = ReportAssemblyAgent(
    name="ReportAssemblyAgent",
    description="Deterministically assembles and validates the final SV report.",
)

root_agent = SequentialAgent(
    name="SVInvestigationPipeline",
    description="Runs a fixed baseline plus a bounded, auditable adaptive investigation.",
    sub_agents=[
        input_normalizer_agent,
        baseline_evidence_agent,
        adaptive_investigation_agent,
        literature_agent,
        evidence_synthesis_agent,
        evidence_verifier_agent,
        report_assembly_agent,
    ],
)
