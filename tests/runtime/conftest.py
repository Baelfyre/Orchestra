def pytest_pycollect_makeitem(collector, name, obj):
    """Do not collect imported runtime helpers that merely happen to start with test_."""
    if (
        name == "test_evidence_main"
        and getattr(obj, "__module__", None) == "orchestra_runtime.test_evidence"
    ):
        return []
    return None
