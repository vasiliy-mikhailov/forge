# `test_when_game_result_constructed_then_fields_preserved`

Pins the `GameResult` data contract. One constructor call, every
field reads back exactly the value passed in, frozen-ness holds.

- **Arrange**: import `GameResult` from
  `src.tier1.entities.game_result`.
- **Act**: construct
  `GameResult(seed=1000, score=7211, max_tile=512, moves=614,
  final_state='lost', walltime_sec=0.182)`.
- **Assert**: every field reads back its constructor value; the
  dataclass is frozen (attempted mutation raises
  `FrozenInstanceError`).

Test code: [`tests/tier1/entities/test_game_result.py`](../../../../tests/tier1/entities/test_game_result.py).
