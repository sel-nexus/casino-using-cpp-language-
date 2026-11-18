"""Verify the Python-only release boundary and maintainer instructions."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_cpp_application_and_harness_are_retired() -> None:
    """Reject a release containing an unmigrated native implementation."""
    assert not (ROOT / "main (1).cpp").exists()
    assert not (ROOT / "tests.cpp").exists()
    assert not list(ROOT.glob("*.cpp"))


def test_both_python_launch_commands_are_documented() -> None:
    """Verify maintainers can find both real launch adapters."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "python3 main.py" in readme
    assert "python3 -m casino" in readme
    assert (ROOT / "main.py").is_file()
    assert (ROOT / "casino" / "__main__.py").is_file()


def test_migration_notes_preserve_payout_and_document_eof_fix() -> None:
    """Require explicit compatibility evidence rather than silent changes."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "no initial stake deduction" in readme
    assert "EOF no longer causes an endless prompt loop" in readme
    assert "879d6ca51f7af7054c6c88e7ba226d442a90876f" in changelog
    assert "No data or configuration migration" in changelog
