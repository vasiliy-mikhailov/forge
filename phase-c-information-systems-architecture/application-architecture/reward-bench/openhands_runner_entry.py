#!/usr/bin/env python3
"""§4 SolutionGenerator entrypoint — runs inside the
reward-bench-openhands-runner image.

Reads the rendered prompt from stdin, runs an OpenHands
Conversation against the vLLM endpoint configured via the
OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL_ID environment
variables, then prints the agent's last assistant message text
to stdout.

The host's `timeout N docker run ...` wrapper enforces wallclock.
On SIGTERM this script's process dies; any partial stdout flushed
before SIGTERM survives. The agent's tool calls die with the
container.
"""
from __future__ import annotations

import os
import sys
import tempfile


def main() -> int:
    from openhands.sdk import LLM, Agent, Conversation
    from openhands.sdk.event import MessageEvent
    from openhands.tools.preset.default import (
        get_default_tools, register_default_tools,
    )

    prompt = sys.stdin.read()
    if not prompt.strip():
        return 0  # nothing to do; empty stdout → host body == ''

    register_default_tools(enable_browser=False)
    tools = get_default_tools(enable_browser=False)

    base_url = os.environ['OPENAI_BASE_URL'].rstrip('/')
    if not base_url.endswith('/v1'):
        base_url = base_url + '/v1'

    llm = LLM(
        model=f'openai/{os.environ["OPENAI_MODEL_ID"]}',
        api_key=os.environ['OPENAI_API_KEY'],
        base_url=base_url,
        usage_id='reward-bench-solution-generator',
    )
    agent = Agent(llm=llm, tools=tools)

    with tempfile.TemporaryDirectory() as td:
        conv = Conversation(agent=agent, workspace=td)
        conv.send_message(prompt)
        conv.run()

        # Find the last agent MessageEvent, print its text content
        # to stdout. extract_fenced_python on the host lifts the
        # body.
        for event in reversed(list(conv.state.events)):
            if not isinstance(event, MessageEvent):
                continue
            if getattr(event, 'source', None) != 'agent':
                continue
            for c in getattr(event.llm_message, 'content', []) or []:
                t = getattr(c, 'text', None)
                if t:
                    print(t, flush=True)
            break

    return 0


if __name__ == '__main__':
    sys.exit(main())
