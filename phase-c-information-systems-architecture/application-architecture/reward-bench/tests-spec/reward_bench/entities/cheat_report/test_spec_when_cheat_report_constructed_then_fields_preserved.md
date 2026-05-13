# `test_when_cheat_report_constructed_then_fields_preserved`

Pins the `CheatReport` data contract — the verdict envelope around
`CheatFinding` rows. Mirrors SPEC.md pydantic schema.

- **Arrange**: import `CheatReport`, `CheatFinding`.
- **Act**: construct `CheatReport(findings=(f1, f2),
  network_policy='vllm_only', replay_score_match=True,
  replay_tolerance_pct=5.0, verdict='warning', rejected_reason=None)`.
- **Assert**: every field reads back its constructor value;
  `len(report.findings) == 2`.

Test code: [`tests/reward_bench/entities/test_cheat_report.py`](../../../../tests/reward_bench/entities/test_cheat_report.py).
