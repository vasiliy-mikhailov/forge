# \`src_spec_when_reply_inspected_then_contains_one_fenced_python_block\`

\`src.adapters.parser.has_fenced_python_block(reply: str) -> bool\`
returns True iff \`reply\` contains a fenced Python code block of the
shape:

    \`\`\`python
    ...
    \`\`\`

The language tag (\`python\`) MAY be omitted; a bare \`\`\`...\`\`\`
fence also counts (vLLM and reasoning models sometimes drop the
language tag). Indentation before the fence is tolerated.
