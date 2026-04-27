"""
Step 3 — sub-agent does file I/O.

source-author has terminal + file_editor. System prompt instructs:
"You will receive a source index N in your task. Create /workspace/source-{N}/
and write a file output.md inside it with content 'STEP3_OK_{N}'."

Orchestrator delegates with N=0. Asserts file exists and content matches.
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


WORKDIR = Path("/tmp/step3-orch-ws")


def main():
    source_author = AgentDefinition(
        name="source-author",
        description="Step 3 stub — writes a file under source-{N}/.",
        tools=["terminal", "file_editor"],
        system_prompt=(
            "You are source-author. Your task message will tell you a source "
            "index N (an integer 0..6). For that N you must:\n"
            "  1. Create the directory source-{N} (use the terminal "
            "tool: mkdir -p source-{N}).\n"
            "  2. Use file_editor to create source-{N}/output.md with "
            "the EXACT literal content 'STEP3_OK_N' (substitute {N} with the "
            "integer; e.g. for N=0 the content is exactly 'STEP3_OK_0').\n"
            "  3. Call finish with the message 'done'.\n"
            "Do not add any other content, prose, or trailing newlines beyond "
            "the literal STEP3_OK_N."
        ),
    )

    register_agent(
        name=source_author.name,
        factory_func=agent_definition_to_factory(source_author),
        description=source_author,
    )
    register_tool("DelegateTool", DelegateTool)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step3",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(
        agent=main_agent,
        workspace=str(WORKDIR),
        visualizer=DelegationVisualizer(name="OrchStep3"),
    )

    conv.send_message(
        "Use the DelegateTool to spawn a sub-agent with id 'src0' of agent type "
        "'source-author', then delegate to it: 'Process source N=0. Follow your "
        "system prompt instructions for N=0.' "
        "Once it returns 'done', finish yourself."
    )
    conv.run()

    # Assert: file exists with exact content
    expected = WORKDIR / "source-0" / "output.md"
    if not expected.exists():
        print(f"\n=== STEP 3 FAIL: file not created at {expected} ===", file=sys.stderr)
        sys.exit(1)
    content = expected.read_text().strip()
    if content == "STEP3_OK_0":
        print(f"\n=== STEP 3 PASS: {expected} contains exactly 'STEP3_OK_0' ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 3 FAIL: content is {content!r}, expected 'STEP3_OK_0' ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
