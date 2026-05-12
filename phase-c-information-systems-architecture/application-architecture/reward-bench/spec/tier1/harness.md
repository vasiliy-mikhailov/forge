# Tier 1 harness

## Purpose

Load a Tier 1 submission (a Python module with class Solver) from
disk so the harness can run games against it.

## Public function

    load_submission(path: Path) -> type

Returns the Solver class declared in the module at path.

## Contract (current scope)

For a module at path that defines class Solver, load_submission imports
the module in an isolated namespace and returns the Solver class.

## Out of scope (deferred)

- Anti-cheat checks before load
- Sandbox isolation (currently loads in-process)
- Modules without class Solver
- Modules that raise on import
- Multiple Solver classes (only the one named Solver is returned)
