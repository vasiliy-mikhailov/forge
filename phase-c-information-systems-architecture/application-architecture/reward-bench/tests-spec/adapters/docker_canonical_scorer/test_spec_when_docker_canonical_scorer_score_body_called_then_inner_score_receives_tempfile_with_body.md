# `test_when_docker_canonical_scorer_score_body_called_then_inner_score_receives_tempfile_with_body`

Pins the §7.5 body-in API on the production canonical scorer per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7.5. `score_body` is the file-API-free entry point: the body
string is the input; the Docker bind-mount tempfile is materialised
INSIDE this method and never escapes.

For unit testability the test injects a recording stub over the
underlying `.score(submission_path, ...)` method (which still
exists during the migration). The stub captures the path it
receives and reads its contents; the test asserts the contents
match the body input.

- **Arrange**: `scorer = DockerCanonicalScorer()`; monkeypatch
  `scorer.score` with a recording stub that captures
  `submission_path` and returns a stub `AttemptResult`.
- **Act**: `scorer.score_body(body='class Solver: pass\n',
  seeds=(1,))`.
- **Assert**: the captured `submission_path` exists (during the
  call); `Path(submission_path).read_text() == 'class Solver: pass\n'`.

Test code: [`../../../tests/adapters/test_docker_canonical_scorer.py`](../../../tests/adapters/test_docker_canonical_scorer.py)::`test_when_docker_canonical_scorer_score_body_called_then_inner_score_receives_tempfile_with_body`.

## Model client injection point

- **Seam**: monkeypatch on the scorer instance's `.score` method.
- **Mode**: **fake** — no Docker spawn; stub intercepts.

## Runtime scope

> **Runtime scope**: unit only — tempfile marshalling test; no Docker run.
