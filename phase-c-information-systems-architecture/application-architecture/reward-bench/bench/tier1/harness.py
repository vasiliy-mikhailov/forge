"""Tier 1 harness. See spec/tier1/harness.md."""
import importlib.util


def load_submission(path):
    spec = importlib.util.spec_from_file_location('submission', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Solver
