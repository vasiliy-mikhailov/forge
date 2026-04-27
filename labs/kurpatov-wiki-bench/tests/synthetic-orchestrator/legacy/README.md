# Legacy synth orchestrator TDD ladder

Progressive TDD checkpoints from D7-rev3 → D7-rev4-v2 → D8.
Each step was the GREEN gate at the time it landed. All
superseded by:

- `../step7_orchestrator.py` — Python-loop + concept v3 (D8 step 0+0.2)
- `../step8_smoke.py` — retrieval helpers smoke (D8 step 1-3)

Do NOT add new tests under `legacy/`. Add to current step7/8
or create step9+ at the parent directory.
