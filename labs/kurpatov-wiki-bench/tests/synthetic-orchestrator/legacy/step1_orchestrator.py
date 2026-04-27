"""
Step 1 — delegation hello-world.

Main agent: has DelegateTool. Asked to delegate "say HELLO_FROM_SUB_AGENT" to the
default builtin subagent. We capture all events and assert the magic token appears
in the subagent's terminal output (or in any sub-agent message).

Pass criterion: HELLO_FROM_SUB_AGENT appears in conversation events.
"""
import os
import sys
from pathlib import Path

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.sdk.tool import register_tool
from openhands.tools import register_builtins_agents
from openhands.tools.delegate import DelegateTool, DelegationVisualizer


def main():
    # 1. Register builtin subagents (default, code_explorer, bash_runner, web_researcher)
    register_builtins_agents()

    # 2. Register delegate tool
    register_tool("DelegateTool", DelegateTool)

    # 3. LLM from env
    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step1",
    )

    # 4. Main agent with only DelegateTool
    main_agent = Agent(
        llm=llm,
        tools=[Tool(name="DelegateTool")],
    )

    # 5. Conversation
    workdir = Path("/tmp/step1-orch-ws")
    workdir.mkdir(parents=True, exist_ok=True)
    conv = Conversation(
        agent=main_agent,
        workspace=str(workdir),
        visualizer=DelegationVisualizer(name="OrchStep1"),
    )

    # 6. Send the orchestration message
    conv.send_message(
        "Use the DelegateTool to spawn a sub-agent with id 'hello' (default agent type), "
        "then delegate to it the task: 'Print the literal token HELLO_FROM_SUB_AGENT to the "
        "terminal using your terminal tool, then finish.' "
        "After it returns, finish yourself with a one-line summary."
    )
    conv.run()

    # 7. Inspect events for the magic token. Events are pydantic models;
    # Convert to JSON to get full content of all nested fields.
    import json
    events_json = json.dumps([ev.model_dump(mode="json") for ev in conv.state.events],
                             default=str, ensure_ascii=False)

    if "HELLO_FROM_SUB_AGENT" in events_json:
        print("\n=== STEP 1 PASS: HELLO_FROM_SUB_AGENT present in events ===")
        sys.exit(0)
    else:
        print("\n=== STEP 1 FAIL: token not found in events ===", file=sys.stderr)
        print("--- last 2000 chars of events_text ---", file=sys.stderr)
        print(events_text[-2000:], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
