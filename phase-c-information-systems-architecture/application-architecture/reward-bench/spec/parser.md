# Parser

## Purpose

Extract tool calls emitted by the model from the assistant reply text.

## Tool-call wire format

The model encodes one tool call as a fenced block:

    ```tool
    {"name": "<tool-name>", "args": {<key>: <value>, ...}}
    ```

## Public function

    parse_tool_calls(text: str) -> list[tuple[str, dict[str, str]]]

## Contract (current scope)

Given a reply containing exactly one well-formed closed tool fence
whose body is a valid JSON object with a non-empty string "name"
and a dict "args", parse_tool_calls returns a single-element list:

    [(name, args)]

Behaviors outside this scope (BPE detokenization, body region after
===FILE_BODY===, trailing unclosed fence, malformed JSON tolerance,
arg value coercion) are not yet specified. They will be added as the
corresponding test cases are introduced.
