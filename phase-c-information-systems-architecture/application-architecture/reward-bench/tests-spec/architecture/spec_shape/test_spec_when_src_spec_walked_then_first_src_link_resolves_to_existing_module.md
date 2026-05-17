# `test_when_src_spec_walked_then_first_src_link_resolves_to_existing_module`

Architecture / fitness-function. Every `src_spec_*.md` must name
the `src/` module it describes via a markdown link
(`[`src/X.py`](relative-path)`). This test parses the first such
link and asserts the file exists.

Ratchet: `EXPECTED_MAX_SRC_LINK_VIOLATIONS` decremented per cycle.

## Contract

- **Arrange**: discover all `src_spec_*.md` under `src-spec/`.
- **Act**: for each, find the first `[`...src/...py`](...)` link;
  resolve relative to the spec dir; check existence.
- **Assert**: `len(violations) <= EXPECTED_MAX_SRC_LINK_VIOLATIONS`.

## Model client injection point

- **Seam**: none — pure filesystem walk + regex.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_src_spec_walked_then_first_src_link_resolves_to_existing_module`.

## Runtime scope

> **Runtime scope**: unit only.
