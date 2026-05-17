# `src_spec_when_extracted_module_loaded_then_exposes_class_solver`
`src.tier1.harness.load_submission(path)` imports the Python module at
`path` in an isolated namespace via `importlib.util.spec_from_file_location`
and returns the module object. Callers retrieve the Solver class via
`module.Solver`.
If the module raises during import, the exception propagates (no
swallowing — failed imports are real failures and must surface).
