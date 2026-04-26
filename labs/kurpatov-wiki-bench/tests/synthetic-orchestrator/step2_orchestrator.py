"""
Step 2 — custom AgentDefinition for source-author.

Define a minimal AgentDefinition with name="source-author" and a trivial
system prompt. Register it. Orchestrator delegates to it; assertion checks
the magic token appears.
"""
import os
import sys
import json
from pathlib import Path

from openhands.sdk import (
    LLM, Agent, Conversation, Tool,
    register_agent, agent_definition_to_factory,
)
from openhands.sdk.subagent import AgentDefinition
from openhands.sdk.tool import register_tool
from openhands.tools.delegate import DelegateTool, DelegationVisualizer


def main():
    # 1. Define a minimal source-author subagent
    source_author = AgentDefinition(
        name="source-author",
        description="Echoes whatever the orchestrator asks. (Step 2 stub)",
        tools=["terminal"],
        system_prompt=(
            "You are source-author, a sub-agent stub for the D7-rev3 experiment.\n"
            "Whatever the orchestrator's task says to do, do it via the terminal "
            "tool, then call finish with one short message.\n"
            "Do not add any extra prose. Just execute literally."
        ),
    )

    # 2. Register it as a delegate target
    register_agent(
        name=source_author.name,
        factory_func=agent_definition_to_factory(source_author),
        description=source_author,
    )

    # 3. Register the delegate tool
    register_tool("DelegateTool", DelegateTool)

    # 4. LLM
    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step2",
    )

    # 5. Orchestrator
    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    workdir = Path("/tmp/step2-orch-ws")
    workdir.mkdir(parents=True, exist_ok=True)
    conv = Conversation(
        agent=main_agent,
        workspace=str(workdir),
        visualizer=DelegationVisualizer(name="OrchStep2"),
    )

    # 6. Delegate to source-author
    conv.send_message(
        "Use the DelegateTool to spawn a sub-agent with id 'src5' of agent type "
        "'source-author', then delegate to it the task: 'Print the literal token "
        "SOURCE_AUTHOR_ALIVE to the terminal.' "
        "Once it returns, finish."
    )
    conv.run()

    # 7. Assert
    events_json = json.dumps([ev.model_dump(mode="json") for ev in conv.state.events],
                             default=str, ensure_ascii=False)
    if "SOURCE_AUTHOR_ALIVE" in events_json:
        print("\n=== STEP 2 PASS: SOURCE_AUTHOR_ALIVE present in events ===")
        sys.exit(0)
    else:
        print("\n=== STEP 2 FAIL ===", file=sys.stderr)
        print(events_json[-2000:], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
