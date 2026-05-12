# Parser

## Purpose

Extract tool calls emitted by the model from the assistant reply text.

## Tool-call wire format

The model encodes one tool call as a fenced block whose body is JSON:

    ```tool
    BODY
    ```

## Public function

    parse_tool_calls(text)

## Contract (current scope)

For a reply containing exactly one closed tool fence whose body is
JSON that decodes to a dict containing keys "name" and "args"
(where "args" is also a dict), parse_tool_calls returns a list of
length 1:

    [(body["name"], body["args"])]

Values inside "args" are returned unchanged.

## Out of scope (deferred to future cycles)

- BPE detokenization (Ġ, Ċ, ĉ byte-pair markers)
- Empty "name"
- Non-string "name"
- Non-dict "args"
- Top-level body is not a dict (list, string, number)
- Body separator after ===FILE_BODY=== or ---
- Trailing unclosed fence fallback
- Malformed JSON tolerance (trailing comma, syntax errors)
- Multiple fences in one reply
- Arg value coercion (non-string values stringified)
- No fence in reply at all

Behavior on inputs outside the current scope is unspecified.
