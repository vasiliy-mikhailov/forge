# `test_when_condenser_config_constructed_then_fields_preserved`

Pins the `CondenserConfig` data contract — the orchestrator-side
configuration for the context-compaction step described in SPEC.md
("A condenser summarises older turns when prompt + reserved output
exceeds the budget"). Mirrors the `--condenser-*` flags from the
legacy `_bak/bin/campaign_tier1.sh` script.

- **Arrange**: import `CondenserConfig`.
- **Act**: construct `CondenserConfig(trigger_tokens=40000,
  keep_recent=8, model_id='condenser-llama31-8b')`.
- **Assert**: every field reads back its constructor value;
  dataclass is frozen.

Test code: [`tests/reward_bench/entities/test_condenser_config.py`](../../../../tests/reward_bench/entities/test_condenser_config.py).
