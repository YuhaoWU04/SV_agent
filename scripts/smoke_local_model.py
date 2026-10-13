"""Live adapter check: tool execution/state, then Pydantic JSON output.

Run from the repository's parent: python -m sv_investigator.scripts.smoke_local_model
with SV_AGENT_MODEL_BACKEND=litellm and a local server configured.
"""

import asyncio
import json
from pathlib import Path

from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types
from pydantic import BaseModel

from sv_investigator.config import MODEL, MODEL_BACKEND, build_model


class SmokeOutput(BaseModel):
    status: str


def choose_tool(callback_context, llm_request):
    # Require one call to test the adapter, not this tiny model's planning skill.
    mode = "NONE" if "tool_marker" in callback_context.state else "ANY"
    llm_request.config.tool_config = types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(mode=mode)
    )


def ping(value: str, tool_context: ToolContext) -> dict:
    """Save and echo a value."""
    tool_context.state["tool_marker"] = value
    return {"value": value}


async def main():
    assert MODEL_BACKEND == "litellm", "Configure the local backend first"
    model = build_model()
    pipeline = SequentialAgent(name="LocalSmoke", sub_agents=[
        Agent(
            name="ToolSmoke", model=model,
            instruction="Call ping with value hello. Then say done.",
            tools=[ping], before_model_callback=choose_tool,
            generate_content_config=types.GenerateContentConfig(temperature=0, max_output_tokens=128),
        ),
        Agent(
            name="JsonSmoke", model=model, include_contents="none",
            instruction='Return status="ok" as JSON.',
            output_schema=SmokeOutput, output_key="smoke_output",
            generate_content_config=types.GenerateContentConfig(temperature=0, max_output_tokens=128),
        ),
    ])
    sessions = InMemorySessionService()
    await sessions.create_session(app_name="local_smoke", user_id="test", session_id="test")
    runner = Runner(app_name="local_smoke", agent=pipeline, session_service=sessions)
    events = []
    async for event in runner.run_async(
        user_id="test", session_id="test",
        new_message=types.Content(role="user", parts=[
            types.Part.from_text(text="Call ping with value hello.")
        ]),
    ):
        events.append(event.model_dump(mode="json", exclude_none=True))
    session = await sessions.get_session(app_name="local_smoke", user_id="test", session_id="test")
    state = dict(session.state)
    destination = Path(__file__).resolve().parents[1] / "output/local-model-test/smoke.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"model": MODEL, "state": state, "events": events},
        ensure_ascii=False, indent=2), encoding="utf-8")
    assert state["tool_marker"] == "hello", state
    output = SmokeOutput.model_validate(state["smoke_output"])
    assert output.status == "ok", output
    destination.write_text(json.dumps({"model": MODEL, "passed": True,
        "checks": ["tool_call", "tool_state", "structured_output"],
        "state": state, "events": events}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS: tool call, state, structured output; artifacts: {destination}")


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=120))
