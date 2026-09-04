from pathlib import Path

import pytest

from slog.parser import parse_report

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_run1_result_count():
    run = parse_report(FIXTURES / "run1.json")
    assert len(run.results) == 3


def test_parse_timestamps():
    run = parse_report(FIXTURES / "run1.json")
    assert run.timestamp.year == 2023


def test_parse_environment():
    run = parse_report(FIXTURES / "run1.json")
    assert run.environment == "linux"


def test_parse_passed_status():
    run = parse_report(FIXTURES / "run1.json")
    passed = [r for r in run.results if r.status == "passed"]
    assert len(passed) == 1
    assert passed[0].name == "tests/test_login.py::test_login_success"


def test_parse_failed_status():
    run = parse_report(FIXTURES / "run1.json")
    failed = run.failed
    assert len(failed) == 2


def test_parse_error_message_present():
    run = parse_report(FIXTURES / "run1.json")
    regression = next(r for r in run.results if "test_login_invalid" in r.name)
    assert regression.error_message is not None
    assert "AssertionError" in regression.error_message or "assert" in regression.error_message


def test_normalized_error_strips_paths():
    run = parse_report(FIXTURES / "run1.json")
    regression = next(r for r in run.results if "test_login_invalid" in r.name)
    normalized = regression.normalized_error
    assert "/app/tests/test_login.py" not in normalized
    assert "<path>" in normalized


def test_likely_cause_assertion_is_regression():
    run = parse_report(FIXTURES / "run1.json")
    r = next(t for t in run.results if "test_login_invalid" in t.name)
    assert r.likely_cause == "likely_regression"


def test_likely_cause_timeout_is_flaky():
    run = parse_report(FIXTURES / "run1.json")
    r = next(t for t in run.results if "test_banner_visible" in t.name)
    assert r.likely_cause == "likely_flaky"


def test_pass_rate():
    run = parse_report(FIXTURES / "run1.json")
    assert run.pass_rate == pytest.approx(1 / 3)


def test_source_file_recorded():
    path = FIXTURES / "run1.json"
    run = parse_report(path)
    assert run.source_file == str(path)
