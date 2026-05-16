# `test_when_extracted_module_loaded_then_exposes_class_solver`

Pins harness layer L5.1: the model's submission, once written to a
file and imported, exposes a `class Solver`.

- **Arrange**: session-scoped `skill_tier1_reply` fixture (live model
  call). Extract Python source via `src.tier1.adapters.parser.extract_python`.
- **Act**: call `src.tier1.harness.load_submission(path_to_temp_py)`
  on the extracted source written to a temp file.
- **Assert**: the loaded module attribute `Solver` exists and is a
  class.

Test code: [`tests/tier1/test_harness.py`](../../tests/tier1/test_harness.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

