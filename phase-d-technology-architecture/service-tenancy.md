# Service tenancy — forge-wide vs lab-local

Some technology services are provided centrally and consumed by
every lab; some live inside one lab. The split decides where a
change lands.

| Service                                      | Provided by                                      | Consumed by                                  |
|----------------------------------------------|--------------------------------------------------|----------------------------------------------|
| Container runtime + GPU isolation            | host (Docker + nvidia-container-toolkit)         | every lab                                    |
| Persistence-aware GPU power mgmt             | host (`nvidia-power-limit.service`)              | every GPU-using lab                          |
| Reverse proxy + TLS termination              | per-lab caddy (mutex on host :80/:443)           | the lab's own public services                |
| Source-of-truth + per-experiment branches    | GitHub remotes                                   | every lab                                    |
| LLM inference                                | `wiki-compiler` (vLLM)                           | `wiki-bench`, future RL trainers             |
| Audio → text transcription                   | `wiki-ingest` (faster-whisper)                   | `kurpatov-wiki-wiki` source-of-truth         |
| Agent orchestration & sub-agent delegation   | `wiki-bench` (OpenHands SDK)                     | bench's per-source pipelines                 |
| Vector retrieval (claim/concept dedup)       | `wiki-bench` (`embed_helpers.py`)                | bench's source-author + curator              |
| ML training tracking                         | `rl-2048/mlflow/` (MLflow)                       | rl-2048 only                                 |
| Notebook sandbox                             | `rl-2048/jupyter/`                               | rl-2048 only                                 |
| LoRA / RFT fine-tuning                       | `rl-2048` (unsloth, planned)                     | rl-2048 only (currently)                     |

**Rule.** If a component appears in column 2 of more than one row
it is forge-wide. (Caddy is the obvious case — every lab runs its
own, but they share the same host-port-mutex constraint, so caddy
itself is a forge-wide concern even though instances are
lab-local.)

Specific version pins live in `Dockerfile`s and `.env` files;
specific *decisions* about why those versions/components were
picked live in lab ADRs.
