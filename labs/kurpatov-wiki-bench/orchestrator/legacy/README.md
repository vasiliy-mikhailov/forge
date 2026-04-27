# Legacy orchestrator drivers

Kept for diff reference only. Canonical driver is
`../run-d8-pilot.py` (Python-loop top-orch + canonical
skill v2 concept shape, ADR 0010).

| file               | era       | status      | superseded-by    |
|--------------------|-----------|-------------|------------------|
| run-d7-rev3.py     | D7-rev3   | partial 4/7 | run-d8-pilot.py  |
| run-d7-rev4.py     | D7-rev4   | aborted     | run-d8-pilot.py  |
| run-d7-rev4-v2.py  | D7-rev4-v2| 5/7         | run-d8-pilot.py  |

Do NOT use these as reference for new work. They use DelegateTool
(deprecated) or single-Conversation top-orch (broken at scale).
See ADR 0009 (superseded by 0010) and STATE-OF-THE-LAB.md.
