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

For a reply containing no tool fence at all, parse_tool_calls
returns an empty list.

For a reply containing N well-formed closed tool fences in document
order, parse_tool_calls returns a list of N tuples in the same order.

Before matching fences, parse_tool_calls substitutes BPE byte-pair
marker U+0120 (Ġ) with a literal space. This is needed because some
HF-format Mistral quants leak the marker between JSON tokens, where
it is not valid whitespace and would otherwise break json.loads.

## Out of scope (deferred to future cycles)

- BPE detokenization of Ċ (newline) and ĉ (tab) markers
- Empty "name"
- Non-string "name"
- Non-dict "args"
- Top-level body is not a dict (list, string, number)
- Body separator after ===FILE_BODY=== or ---
- Trailing unclosed fence fallback
- Malformed JSON tolerance (trailing comma, syntax errors)
- Arg value coercion (non-string values stringified)

Behavior on inputs outside the current scope is unspecified.
