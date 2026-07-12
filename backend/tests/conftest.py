"""Shared pytest configuration and test-tier classification.

Test tiers are derived from file names so individual test modules do not need
repetitive decorators.  A test can still add a more specific marker locally.
"""

from pathlib import Path

_SLOW_FILES = {
    "test_classify_concurrency.py",
    "test_classify_timeout.py",
    "test_cv_processor.py",
    "test_gmail_adapter.py",
    "test_review_service.py",
}


def pytest_collection_modifyitems(items: list[object]) -> None:
    """Classify collected tests for fast PR and full-suite CI runs."""
    tests_root = Path(__file__).parent

    for item in items:
        path = Path(str(item.fspath))
        relative_path = path.relative_to(tests_root).as_posix().lower()
        filename = path.name.lower()

        if "property" in filename:
            item.add_marker("property")
        if filename in _SLOW_FILES:
            item.add_marker("slow")

        if any(token in relative_path for token in ("integration", "e2e", "migration")):
            item.add_marker("integration")
        if "migration" in relative_path:
            item.add_marker("migration")
        if "e2e" in relative_path:
            item.add_marker("e2e")
