import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from sv_investigator.state_pipeline import (
    prepare_verification_evidence, query_verification_evidence,
    reconcile_verification_from_state, normalize_and_store,
)


class VerifierLookupTest(unittest.TestCase):
    def state(self):
        rows = [
            {"evidence_id": "ENS-BL-NOMINAL-REPEAT-001", "description": "L4_A_Mam",
             "feature_type": "repeat", "breakpoint_role": "nominal", "start": 900, "end": 1200, "chrom": "3"},
            {"evidence_id": "ENS-BL-START-REPEAT-002", "description": "dust",
             "feature_type": "repeat", "breakpoint_role": "start", "start": 800, "end": 850, "chrom": "3"},
        ]
        state = {"baseline_evidence": {"region_annotation": {"source": "Ensembl", "status": "found",
            "records": rows, "limitations": ["window hits are contextual"]}},
            "claim_synthesis": {"candidate_claims": [{"claim_id": "C1", "text": "L4 overlap",
                "claim_type": "database_fact", "report_section": "gene_region_annotation",
                "evidence_ids": [rows[0]["evidence_id"]]}]}}
        prepare_verification_evidence(state)
        return state

    def test_complete_store_and_compact_directory(self):
        state = self.state()
        self.assertEqual(len(state["evidence_view"]["records_by_id"]), 2)
        view = state["verification_evidence_view"]
        self.assertNotIn("records_by_id", view)
        self.assertEqual(len(view["directory"]), 2)
        result = query_verification_evidence(state, evidence_ids=[view["cited_ids"][0]])
        self.assertEqual(result["records_by_id"][view["cited_ids"][0]]["record"]["description"], "L4_A_Mam")
        self.assertEqual(result["records_by_id"][view["cited_ids"][0]]["context"]["limitations"], ["window hits are contextual"])

    def test_search_scope_interval_and_literal_matching(self):
        state = self.state()
        original = copy.deepcopy(state["baseline_evidence"])
        result = query_verification_evidence(state, source_prefix="ENS", feature_type="repeat", text="DUST")
        self.assertEqual(result["total_matches"], 1)
        self.assertEqual(result["directory"][0]["breakpoint_role"], "start")
        self.assertEqual(query_verification_evidence(state, text="dust", chrom="chr3", start=1000, end=1050)["total_matches"], 0)
        self.assertEqual(query_verification_evidence(state, scope="nominal")["total_matches"], 1)
        self.assertEqual(query_verification_evidence(state, text=".*")["total_matches"], 0)
        self.assertEqual(state["baseline_evidence"], original)

    def test_pagination_validation_and_deduplication_without_call_quota(self):
        state = self.state()
        page = query_verification_evidence(state, limit=1)
        self.assertTrue(page["truncated"])
        next_page = query_verification_evidence(state, limit=1, offset=page["next_offset"])
        self.assertIsNone(next_page["next_offset"])
        self.assertNotEqual(page["directory"][0], next_page["directory"][0])
        self.assertEqual(query_verification_evidence(state, start=1000, end=1050)["status"], "rejected")
        self.assertEqual(query_verification_evidence(state, evidence_ids=["x"] * 9)["status"], "rejected")
        self.assertEqual(query_verification_evidence(state, evidence_ids="bad")["status"], "rejected")
        for index in range(20):
            self.assertEqual(query_verification_evidence(state, text=f"missing{index}")["status"], "complete")
        repeated = query_verification_evidence(state, text="MISSING19")
        self.assertEqual(repeated["status"], "duplicate_request")
        self.assertNotIn("records_by_id", repeated)
        self.assertEqual(len(state["verification_query_history"]), 22)

    def test_oversized_record_projection_and_unknown_ids(self):
        state = self.state()
        row = state["baseline_evidence"]["region_annotation"]["records"][0]
        row["details"] = {"calls": [{"allele": "A", "large": "x" * 30_000}]}
        eid = row["evidence_id"]
        result = query_verification_evidence(state, evidence_ids=[eid, "unknown"])
        self.assertEqual(result["status"], "partial")
        self.assertNotIn(eid, state["verification_loaded_ids"])
        self.assertLess(len(json.dumps(result)), 24_000)
        result = query_verification_evidence(state, evidence_ids=[eid], fields=["description", "details.calls.0.allele"])
        self.assertEqual(result["records_by_id"][eid]["record"]["details.calls.0.allele"], "A")
        self.assertIn(eid, state["verification_loaded_ids"])
        result = query_verification_evidence(state, evidence_ids=[eid], fields=["missing"])
        self.assertEqual(result["records_by_id"], {})

    def test_unread_claim_cannot_pass_and_new_input_resets_queries(self):
        state = self.state()
        draft = {"publication_allowed": True, "supported_claims": [{"claim_id": "C1",
                 "verification_status": "supported", "confidence": "high"}]}
        result = reconcile_verification_from_state(draft, state)
        self.assertEqual(result["rejected_claims"][0]["verification_status"], "unsupported")
        query_verification_evidence(state, evidence_ids=state["verification_evidence_view"]["cited_ids"])
        repeated = query_verification_evidence(state, evidence_ids=state["verification_evidence_view"]["cited_ids"])
        self.assertEqual(repeated["status"], "duplicate_request")
        self.assertNotIn("records_by_id", repeated)
        self.assertEqual(reconcile_verification_from_state(draft, state)["supported_claims"][0]["verification_status"], "supported")
        normalize_and_store(json.dumps({"genome_build": "GRCh38", "chrom": "1", "start": 10, "end": 20, "sv_type": "DEL"}), state)
        self.assertEqual(state["verification_query_history"], [])
        self.assertEqual(state["verification_loaded_ids"], [])

    def test_tools_are_registered_and_declared(self):
        from google.adk.tools import FunctionTool
        from sv_investigator import agent
        from sv_investigator.agent import (
            evidence_verifier_agent, get_evidence_by_ids, search_stored_evidence, get_info_descriptions,
        )
        self.assertEqual(evidence_verifier_agent.tools,
                         [get_evidence_by_ids, search_stored_evidence, get_info_descriptions])
        self.assertIn(get_info_descriptions, agent.evidence_synthesis_agent.tools)
        for other in (agent.input_normalizer_agent, agent.baseline_evidence_agent,
                      agent.adaptive_investigation_agent, agent.literature_agent):
            self.assertNotIn(get_info_descriptions, other.tools)
        for tool in evidence_verifier_agent.tools:
            self.assertEqual(FunctionTool(tool)._get_declaration().name, tool.__name__)
        state = self.state()
        result = search_stored_evidence(SimpleNamespace(state=state), text="dust")
        fetched = get_evidence_by_ids([result["directory"][0]["evidence_id"]], SimpleNamespace(state=state))
        self.assertEqual(next(iter(fetched["records_by_id"].values()))["record"]["description"], "dust")

    def test_saved_del_regression_when_available(self):
        path = Path(__file__).resolve().parents[1] / "runs/1000g_fst_DEL_pindel_9240_gemini35_functional_evidence/cases/DEL_pindel_9240/state.json"
        if not path.exists():
            self.skipTest("local saved DEL run not available")
        state = json.loads(path.read_text(encoding="utf-8"))
        prepare_verification_evidence(state)
        for label in ("L1ME3G", "dust"):
            result = query_verification_evidence(state, source_prefix="ENS", feature_type="repeat", text=label)
            self.assertGreater(result["total_matches"], 0)
            self.assertTrue(all(r["breakpoint_role"] != "nominal" for r in result["directory"]))
            nominal = query_verification_evidence(state, feature_type="repeat", text=label, scope="nominal")
            self.assertEqual(nominal["total_matches"], 0)


class LookupAgentFlowTest(unittest.IsolatedAsyncioTestCase):
    async def test_tool_loop_and_structured_verdict_without_network(self):
        await self.check_verdict_output(structured_tool=False)

    async def test_set_model_response_is_bound_to_original_claim_without_network(self):
        await self.check_verdict_output(structured_tool=True)

    async def check_verdict_output(self, *, structured_tool):
        from google.adk.agents import Agent
        from google.adk.models.base_llm import BaseLlm
        from google.adk.models.llm_response import LlmResponse
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from sv_investigator.agent import (
            prepare_verifier_lookup, bind_verification_to_synthesis,
            get_evidence_by_ids, search_stored_evidence,
            get_info_descriptions,
        )
        from sv_investigator.tools import normalize_sv_input
        from sv_investigator.prompts import VERIFY
        from sv_investigator.schemas import VerificationOutput

        class ScriptedModel(BaseLlm):
            calls: int = 0

            async def generate_content_async(self, llm_request, stream=False):
                steps = [
                    ("search_stored_evidence", {"text": "dust"}),
                    ("get_evidence_by_ids", {"evidence_ids": ["ENS-BL-START-REPEAT-002", "ENS-BL-NOMINAL-REPEAT-001"]}),
                    ("get_info_descriptions", {"field_ids": ["MC", "NS"]}),
                ]
                if self.calls:
                    assert any(p.function_response for c in llm_request.contents for p in c.parts)
                if self.calls < len(steps):
                    name, args = steps[self.calls]
                    part = types.Part(function_call=types.FunctionCall(name=name, args=args))
                else:
                    info_response = next(p.function_response.response
                        for c in llm_request.contents for p in c.parts
                        if p.function_response and p.function_response.name == "get_info_descriptions")
                    assert info_response["fields"]["MC"] == {
                        "value": "call1", "description": "Merged calls.", "source": "1000g_dictionary"}
                    assert info_response["fields"]["NS"]["value"] == "4"
                    verdict = {"publication_allowed": True,
                        "supported_claims": [{"claim_id": "C1", "text": "Verifier rewrote the claim",
                            "claim_type": "database_fact", "report_section": "population_evidence",
                            "evidence_ids": ["ENS-BL-START-REPEAT-002"], "confidence": "high",
                            "verification_status": "supported", "notes": "dust is a window hit, not nominal overlap"}]}
                    part = (
                        types.Part(function_call=types.FunctionCall(name="set_model_response", args=verdict))
                        if structured_tool else types.Part(text=json.dumps(verdict))
                    )
                self.calls += 1
                assert self.calls <= 4
                yield LlmResponse(content=types.Content(role="model", parts=[part]))

        model = ScriptedModel(model="gemini-3.5-flash")
        agent = Agent(name="lookup_test", model=model, instruction=VERIFY,
            tools=[get_evidence_by_ids, search_stored_evidence, get_info_descriptions], output_schema=VerificationOutput,
            output_key="verification", before_agent_callback=prepare_verifier_lookup,
            after_agent_callback=bind_verification_to_synthesis, include_contents="none")
        service = InMemorySessionService()
        initial_state = VerifierLookupTest().state()
        initial_state["normalized_sv"] = normalize_sv_input(json.dumps({"genome_build": "GRCh38",
            "chrom": "3", "start": 1000, "end": 1050, "sv_type": "DEL",
            "source_record": {"dataset": "1000G-SV", "INFO": {"MC": "call1", "NS": "4"}}}))
        await service.create_session(app_name="lookup_test", user_id="test", session_id="one",
                                     state=initial_state)
        runner = Runner(app_name="lookup_test", agent=agent, session_service=service)
        try:
            async for _ in runner.run_async(user_id="test", session_id="one",
                new_message=types.Content(role="user", parts=[types.Part(text="Verify the stored claim.")])):
                pass
            state = (await service.get_session(app_name="lookup_test", user_id="test", session_id="one")).state
            self.assertEqual(len(state["verification_query_history"]), 2)
            self.assertEqual(len(state["evidence_view"]["records_by_id"]), 2)
            self.assertEqual(state["verification"]["supported_claims"][0]["claim_id"], "C1")
            claim = state["verification"]["supported_claims"][0]
            self.assertEqual(claim["text"], "L4 overlap")
            self.assertEqual(claim["report_section"], "gene_region_annotation")
            self.assertEqual(claim["evidence_ids"], ["ENS-BL-NOMINAL-REPEAT-001"])
        finally:
            await runner.close()


if __name__ == "__main__":
    unittest.main()
