# `test_when_canonical_scorer_port_inspected_then_path_based_score_is_absent`

Final cycle of the §7.5 file-API elimination chain per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7.5. The path-based `.score(submission_path, ...)` is removed from
the `CanonicalScorerPort` Protocol and from all production /
testing adapters. The canonical scorer surface is now purely
body-in.

- **Arrange**: import `CanonicalScorerPort`,
  `FakeCanonicalScorer`, `InProcessCanonicalScorer`,
  `DockerCanonicalScorer`.
- **Act**: check `hasattr(...)` for `.score`.
- **Assert**: Port and Fake and InProcess have NO `.score`
  attribute. DockerCanonicalScorer's path-based method is renamed
  to `_score_path` (private). Only `.score_body` is the public
  body-in API across the manifest.

Test code: [`../../../tests/ports/test_canonical_scorer_port.py`](../../../tests/ports/test_canonical_scorer_port.py)::`test_when_canonical_scorer_port_inspected_then_path_based_score_is_absent`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default).

## Runtime scope

> **Runtime scope**: unit only — attribute presence checks.
