# Test cases — SPEC.md

Each entry is a behavior the bench expects from a model under the
interactive submission protocol (SPEC.md Submission protocols section).

All tests pinned to qwen3.6-27b-awq (current bench target). Multi-model
parameterization will return when test-suite runtime becomes the
bottleneck.

## Tier 1 end-to-end layers (see src-spec/tier1/end_to_end.md)

test_when_vllm_container_serves_then_v1_models_endpoint_responds
  Arrange: docker-resolved base_url of container omega-reptile-vllm-playground
           on the proxy-net network; bench API key from VLLM_API_KEY env.
  Act:     GET {base_url}/v1/models with Authorization: Bearer <api_key>,
           HTTP timeout 10 s.
  Assert:  response status is 200 AND response body is non-empty.

