# Test cases — SPEC.md

Each case here is a behavior the bench expects from a model under the
interactive submission protocol (SPEC.md Submission protocols section).

All tests pinned to qwen3.6-27b-awq (current bench target). Multi-model
parameterization will return when test-suite runtime becomes the
bottleneck.

- test_when_vllm_container_serves_then_v1_models_endpoint_responds
- test_when_v1_models_queried_then_qwen3_6_27b_awq_served_name_present
- test_when_chat_completion_sent_to_qwen_then_response_has_non_empty_content
