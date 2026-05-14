"""MODEL_REGISTRY: tuple of every ModelTarget the bench evaluates.

Single source of truth in Python — mirrors the YAML registry at
phase-c-information-systems-architecture/application-architecture/wiki-compiler/configs/models.yml.
Models marked `bench_skip: true` in the YAML are excluded here.

See src-spec/reward_bench/use_cases/model_registry/."""
from src.reward_bench.entities.model_target import ModelTarget


MODEL_REGISTRY = (
    # Tier A — dense 24-32B, single Blackwell
    ModelTarget(id='qwen3.6-27b-awq', hf_path='cyankiwi/Qwen3.6-27B-AWQ-INT4',
                served_name='qwen3.6-27b-awq', max_model_len=131072,
                tool_call_parser='qwen3_coder'),
    ModelTarget(id='qwen3.6-27b-fp8', hf_path='Qwen/Qwen3.6-27B-FP8',
                served_name='qwen3.6-27b-fp8', max_model_len=262144,
                tool_call_parser='qwen3_xml'),
    ModelTarget(id='qwen3.6-27b-nvfp4', hf_path='sakamakismile/Qwen3.6-27B-NVFP4',
                served_name='qwen3.6-27b-nvfp4', max_model_len=262144,
                tool_call_parser='qwen3_xml'),
    ModelTarget(id='qwen3.5-27b-fp8', hf_path='Qwen/Qwen3.5-27B-FP8',
                served_name='qwen3.5-27b-fp8', max_model_len=131072,
                tool_call_parser='qwen3_xml'),
    ModelTarget(id='qwen3.5-27b-nvfp4', hf_path='kaitchup/Qwen3.5-27B-NVFP4',
                served_name='qwen3.5-27b-nvfp4', max_model_len=131072,
                tool_call_parser='qwen3_xml'),
    ModelTarget(id='qwen3-32b-fp8', hf_path='Qwen/Qwen3-32B-FP8',
                served_name='qwen3-32b-fp8', max_model_len=40960,  # cycle 74: actual model max
                tool_call_parser='qwen3_xml'),
    ModelTarget(id='qwen3-32b-nvfp4', hf_path='nvidia/Qwen3-32B-NVFP4',
                served_name='qwen3-32b-nvfp4', max_model_len=131072,
                tool_call_parser='qwen3_xml'),
    ModelTarget(id='devstral-small-2-24b',
                hf_path='Firworks/Devstral-Small-2-24B-Instruct-2512-nvfp4',
                served_name='devstral-small-2-24b', max_model_len=131072,
                tool_call_parser='mistral'),
    ModelTarget(id='mistral-small-3.2-24b',
                hf_path='RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4',
                served_name='mistral-small-3.2-24b', max_model_len=131072,
                tool_call_parser='mistral'),
    ModelTarget(id='gemma-4-31b-fp8', hf_path='google/gemma-4-31B-it',
                served_name='gemma-4-31b-fp8', max_model_len=131072,
                tool_call_parser='gemma4'),
    ModelTarget(id='gemma-4-31b-nvfp4', hf_path='nvidia/Gemma-4-31B-IT-NVFP4',
                served_name='gemma-4-31b-nvfp4', max_model_len=131072,
                tool_call_parser='gemma4'),
    ModelTarget(id='llama-3.1-8b-nvfp4',
                hf_path='nvidia/Llama-3.1-8B-Instruct-NVFP4',
                served_name='llama-3.1-8b-nvfp4', max_model_len=131072,
                tool_call_parser='llama3_json'),
    ModelTarget(id='gpt-oss-20b', hf_path='openai/gpt-oss-20b',
                served_name='gpt-oss-20b', max_model_len=131072,
                tool_call_parser='openai'),
    ModelTarget(id='gpt-oss-120b', hf_path='openai/gpt-oss-120b',
                served_name='gpt-oss-120b', max_model_len=131072,
                tool_call_parser='openai'),

    # Tier B — dense 49-72B, tight VRAM
    ModelTarget(id='nemotron-super-49b-v1.5-fp8',
                hf_path='nvidia/Llama-3.3-Nemotron-Super-49B-v1.5-FP8',
                served_name='nemotron-super-49b-v1.5-fp8', max_model_len=131072,
                tool_call_parser='hermes'),
    ModelTarget(id='nemotron-super-49b-v1.5-nvfp4',
                hf_path='nvidia/Llama-3_3-Nemotron-Super-49B-v1_5-NVFP4',
                served_name='nemotron-super-49b-v1.5-nvfp4', max_model_len=131072,
                tool_call_parser='hermes'),
    ModelTarget(id='llama-3.3-70b-nvfp4',
                hf_path='nvidia/Llama-3.3-70B-Instruct-NVFP4',
                served_name='llama-3.3-70b-nvfp4', max_model_len=32768,
                tool_call_parser='llama3_json'),
    ModelTarget(id='qwen2.5-72b-nvfp4',
                hf_path='enfuse/Qwen2.5-72B-Instruct-NVFP4',
                served_name='qwen2.5-72b-nvfp4', max_model_len=32768,
                tool_call_parser='hermes'),

    # Tier C — 100B+
    ModelTarget(id='devstral-2-123b',
                hf_path='cyankiwi/Devstral-2-123B-Instruct-2512-AWQ-4bit',
                served_name='devstral-2-123b', max_model_len=131072,
                tool_call_parser='mistral'),
    ModelTarget(id='devstral-2-123b-nvfp4',
                hf_path='BrainForge/Devstral-2-123B-Instruct-2512-NVFP4',
                served_name='devstral-2-123b-nvfp4', max_model_len=32768,
                tool_call_parser='mistral'),
    ModelTarget(id='nemotron-3-super-120b-a12b-nvfp4',
                hf_path='nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4',
                served_name='nemotron-3-super-120b-a12b-nvfp4', max_model_len=32768,
                tool_call_parser='hermes'),
    ModelTarget(id='nemotron-3-super-120b-nvfp4',
                hf_path='nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4',
                served_name='nemotron-3-super-120b-nvfp4', max_model_len=16384,
                tool_call_parser='hermes'),
)
