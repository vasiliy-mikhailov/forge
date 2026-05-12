# Test cases — SPEC.md

Each case here is a behavior the bench expects from a model under the
interactive submission protocol (SPEC.md Submission protocols section).

All tests pinned to qwen3.6-27b-awq (current bench target). Multi-model
parameterization will return when test-suite runtime becomes the
bottleneck.

## Plumbing

- test_when_model_asked_for_a_swipe_then_reply_names_one_direction

## Tier 1 submission

- test_when_model_asked_for_tier1_solver_then_reply_contains_class_solver_using_transitions
- test_when_reference_fsm_loaded_then_exposes_class_solver
- test_when_reference_fsm_solver_instantiated_then_returns_instance
- test_when_reference_fsm_move_called_on_starting_board_then_returns_one_of_wasd
- test_when_reference_fsm_plays_one_game_with_seed_then_score_is_non_negative
- test_when_reference_fsm_plays_20_canonical_games_then_mean_score_above_zero
