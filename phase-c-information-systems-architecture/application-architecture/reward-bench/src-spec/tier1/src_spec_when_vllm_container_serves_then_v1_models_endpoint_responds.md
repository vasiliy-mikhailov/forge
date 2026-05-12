# `src_spec_when_vllm_container_serves_then_v1_models_endpoint_responds`

Lab vLLM container exposes `GET /v1/models` over HTTP on the
`proxy-net` Docker network, accepting bench API key auth, returning
a 200 + non-empty JSON body describing the loaded model.

No bench-side implementation in `src/`; this is purely an
infrastructure invariant the bench depends on.
