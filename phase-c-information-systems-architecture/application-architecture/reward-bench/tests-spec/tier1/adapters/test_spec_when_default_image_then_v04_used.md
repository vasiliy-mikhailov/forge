# `test_when_default_image_then_v04_used`
Pins the module-level default image constant. Catches drift between
`_DEFAULT_IMAGE` in the adapter and the `Dockerfile.tier1` image tag.
## Contract
- **Arrange**: import `_DEFAULT_IMAGE` from
 `src.tier1.adapters.docker_canonical_scorer`.
- **Act**: read the constant.
- **Assert**: `_DEFAULT_IMAGE == 'reward-bench-tier1:0.4'`.
## Model client injection point
- **Seam**: none — pure module-level constant.
- **Mode**: n/a.
- **Marker**: `@pytest.mark.no_fake`.
Test code: [`../../../../tests/tier1/adapters/test_docker_canonical_scorer.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer.py)::`test_when_default_image_then_v04_used`.
## Runtime scope
> **Runtime scope**: unit only.
