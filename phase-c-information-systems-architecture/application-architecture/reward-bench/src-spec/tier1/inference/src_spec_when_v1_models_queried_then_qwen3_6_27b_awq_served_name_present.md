# `src_spec_when_v1_models_queried_then_qwen3_6_27b_awq_served_name_present`

Lab vLLM container is configured with `--served-model-name
qwen3.6-27b-awq` and that id appears in the `/v1/models` response.

No bench-side implementation in `src/`; the bench just reads
`data[].id` and asserts membership.
