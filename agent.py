"""Google ADK SequentialAgent definition for candidate-SV investigation."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from google.adk.agents import Agent, BaseAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.tools import ToolContext
from google.genai import types

from .config import MAX_PUBMED_RECORDS, build_model
from .info_definitions import query_info_descriptions
from .prompts import ADAPTIVE, BASELINE, INTAKE, LITERATURE, SYNTHESIS, VERIFY
from .schemas import SVReport, SynthesisOutput, VerificationOutput
from .state_pipeline import (
    adaptive_and_store,
    baseline_and_store,
    build_evidence_view,
    finalize_report_from_state,
    literature_and_store,
    normalize_and_store,
    prepare_verification_evidence,
    query_verification_evidence,
    reconcile_verification_from_state,
)


def prepare_evidence_view(callback_context: CallbackContext) -> None:
    """Expose one deterministic ID-to-record projection to all later agents."""
    callback_context.state["evidence_view"] = build_evidence_view(
        callback_context.state
    )


def prepare_verifier_lookup(callback_context: CallbackContext) -> None:
    """Prepare a compact directory without replacing the full evidence view."""
    prepare_verification_evidence(callback_context.state)


def bind_verification_to_synthesis(
    callback_context: CallbackContext,
) -> None:
    """Bind saved verdicts after either text or set_model_response output.

    Raw model responses remain in the event log. The tool-generated structured
    response bypasses after_model_callback, so enforce the same state boundary
    after the verifier finishes, not while individual model replies are emitted.
    """
    raw = callback_context.state.get("verification")
    validated = (
        VerificationOutput.model_validate_json(raw)
        if isinstance(raw, str) else VerificationOutput.model_validate(raw)
    )
    callback_context.state["verification"] = reconcile_verification_from_state(
        validated.model_dump(mode="json"), callback_context.state
    )


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
    """Search PubMed and save citations and available abstracts with stable IDs.

    Args:
        query: A traceable PubMed query using coordinates, genes, or SV terms.
        max_records: Maximum citation summaries to return.
    """
    return literature_and_store(query, max_records, tool_context.state)


def get_evidence_by_ids(
    evidence_ids: list[str], tool_context: ToolContext, fields: list[str] | None = None,
) -> dict:
    """Fetch up to eight stored evidence records, with source context.

    Args:
        evidence_ids: Exact local IDs to retrieve. Unknown IDs are explicit errors.
        fields: Optional record fields or dotted paths, e.g. call_details.calls.0.
            Omit for the complete record. Use projections if a record exceeds the size cap.
    """
    if not evidence_ids:
        return {"status": "rejected", "error": "evidence_ids_required"}
    return query_verification_evidence(tool_context.state, evidence_ids=evidence_ids, fields=fields)


def get_info_descriptions(field_ids: list[str], tool_context: ToolContext) -> dict:
    """Check INFO abbreviations when their meaning may be ambiguous or unclear.

    Use this instead of guessing an abbreviation's expansion from memory, especially
    when meanings may differ across datasets. Returns each requested raw value beside
    its saved description and definition source. Read-only, no external queries;
    missing fields and undefined descriptions are explicit. Definitions explain field
    semantics, not independent biological evidence.

    Args:
        field_ids: Exact, case-sensitive INFO names, e.g. ["MC", "NS"]. Batch related fields.
    """
    return query_info_descriptions(tool_context.state.get("normalized_sv"), field_ids)


def search_stored_evidence(
    tool_context: ToolContext, source_prefix: str = "", feature_type: str = "",
    scope: str = "", text: str = "", chrom: str = "", start: int = 0, end: int = 0,
    offset: int = 0, limit: int = 20,
) -> dict:
    """Search stored evidence deterministically; returns a directory, not new database data.

    Args:
        source_prefix: Exact prefix, e.g. ENS, QTL, or DBV; empty means all sources.
        feature_type: Exact feature type, e.g. repeat, gene, or regulatory.
        scope: Exact stored scope/role, e.g. nominal, start, end, or nominal_interval.
        text: Case-insensitive literal substring in the stored record; no regex or fuzzy search.
        chrom: Optional chromosome, with or without chr.
        start: Optional 1-based inclusive lower bound; requires chrom and end.
        end: Optional 1-based inclusive upper bound. Tests stored record interval overlap.
        offset: Zero-based pagination offset.
        limit: Page size, between 1 and 20.
    """
    return query_verification_evidence(tool_context.state, source_prefix=source_prefix,
        feature_type=feature_type, scope=scope, text=text, chrom=chrom,
        start=start, end=end, offset=offset, limit=limit)


llm_model = build_model()

input_normalizer_agent = Agent(
    name="InputNormalizerAgent",
    model=llm_model,
    description="Validates and normalizes one candidate SV without inference.",
    instruction=INTAKE,
    tools=[normalize_sv_input_to_state],
)

baseline_evidence_agent = Agent(
    name="BaselineEvidenceCollectorAgent",
    model=llm_model,
    description=(
        "Runs the required deterministic Ensembl overlap/VEP, gnomAD-SV, ClinGen, "
        "ClinVar, dbVar, DGV, and QC baseline."
    ),
    instruction=BASELINE,
    tools=[collect_baseline_evidence_to_state],
)

adaptive_investigation_agent = Agent(
    name="AdaptiveInvestigationAgent",
    model=llm_model,
    description="Chooses at most two justified follow-ups from a fixed whitelist.",
    instruction=ADAPTIVE,
    tools=[adaptive_followup_query],
    output_key="adaptive_investigation",
)

literature_agent = Agent(
    name="LiteratureAgent",
    model=llm_model,
    description="Runs traceable, evidence-guided PubMed searches.",
    instruction=LITERATURE,
    tools=[search_pubmed_to_state],
    output_key="literature_evidence",
)

# Synthesis receives the full evidence view; verification retrieves stored records
# on demand. ADK 2.9 supports tools together with structured output.
evidence_synthesis_agent = Agent(
    name="EvidenceSynthesisAgent",
    model=llm_model,
    description="Converts collected evidence into atomic candidate claims.",
    instruction=SYNTHESIS,
    output_schema=SynthesisOutput,
    output_key="claim_synthesis",
    before_agent_callback=prepare_evidence_view,
    tools=[get_info_descriptions],
    include_contents="none",
)

evidence_verifier_agent = Agent(
    name="EvidenceVerifierAgent",
    model=llm_model,
    description="Performs claim-level grounding and overinterpretation checks.",
    instruction=VERIFY,
    output_schema=VerificationOutput,
    output_key="verification",
    before_agent_callback=prepare_verifier_lookup,
    tools=[get_evidence_by_ids, search_stored_evidence, get_info_descriptions],
    after_agent_callback=bind_verification_to_synthesis,
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
