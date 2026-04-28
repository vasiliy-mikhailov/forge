# Trajectory model — Level 1 / Level 2

Architecture is organised around capabilities, each with two states:

- **Level 1** = as-is (how the capability works today).
- **Level 2** = to-be (the next planned state).

When Level 2 is reached it **becomes** the new Level 1; the prior
Level 1 description is **deleted from docs**. Git history keeps
every prior level — that is the archive.

## Anti-patterns explicitly rejected

We do not maintain:

- `legacy/` tiers
- `Superseded by NNNN` cross-links
- `archive/` directories
- `Withdrawn` / `Deprecated` / `Closed` status flags

**Presence of text in the working tree means current; absence means
git history.** Every doc reads as if it has always been the truth.
A reader does not need to parse a status field to decide whether to
believe it.

## Where trajectories attach

Trajectories attach to **service quality dimensions** (Phase D) or
**capability quality dimensions** (Phase B), not to components.
Replacing a component (e.g. vLLM 0.19.1 → 0.20) is just the next
step on the same trajectory; "Was vLLM 0.19.1" annotations do not
stay in the working tree.

## Rationale

This rule is what keeps `git diff` of the working tree small as the
architecture matures. Without it, Phase D's services pages would
accumulate one paragraph per past component generation, and the
Level-1 description of each capability would drift into a status
log. By forcing the writer to delete on promotion, we keep every
document at "what is true now."
