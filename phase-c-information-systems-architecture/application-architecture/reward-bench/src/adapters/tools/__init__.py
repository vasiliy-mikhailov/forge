"""Tool adapters — implementations of `src.ports.tool.Tool`.

Created in cycle 114 per the rule-of-three lift: three tools (view,
execute_submission, finish) previously dispatched by switch inside
`Tier1ToolRegistry` were lifted into a `Tool` Protocol and one
adapter per tool.
"""
