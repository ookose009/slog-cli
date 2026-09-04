from pathlib import Path

import pytest

from slog.aggregator import cluster_failures, detect_flaky
from slog.parser import parse_report

FIXTURES = Path(__file__).parent / "fixtures"


def _load_runs():
    return [parse_report(FIXTURES / f) for f in ("run1.json", "run2.json", "run3.json")]


def test_cluster_count():
    runs = _load_runs()
    clusters = cluster_failures(runs)
    # regression (AssertionError) and flaky (TimeoutException) are distinct signatures
    assert len(clusters) >= 2


def test_regression_cluster_occurrences():
    runs = _load_runs()
    clusters = cluster_failures(runs)
    regression = next(c for c in clusters if "AssertionError" in c.signature or "assert" in c.signature.lower())
    # appears in all 3 runs
    assert regression.occurrences == 3


def test_timeout_cluster_occurrences():
    runs = _load_runs()
    clusters = cluster_failures(runs)
    timeout = next(c for c in clusters if "TimeoutException" in c.signature)
    # appears in run1 and run3 only (run2 passed)
    assert timeout.occurrences == 2


def test_cluster_likely_cause_regression():
    runs = _load_runs()
    clusters = cluster_failures(runs)
    regression = next(c for c in clusters if "AssertionError" in c.signature or "assert" in c.signature.lower())
    assert regression.likely_cause == "likely_regression"


def test_cluster_likely_cause_flaky():
    runs = _load_runs()
    clusters = cluster_failures(runs)
    timeout = next(c for c in clusters if "TimeoutException" in c.signature)
    assert timeout.likely_cause == "likely_flaky"


def test_detect_flaky_identifies_banner():
    runs = _load_runs()
    flaky = detect_flaky(runs)
    names = [f.name for f in flaky]
    assert "tests/test_home.py::test_banner_visible" in names


def test_flakiness_score_range():
    runs = _load_runs()
    flaky = detect_flaky(runs)
    for f in flaky:
        assert 0.0 <= f.flakiness_score <= 1.0


def test_deterministic_failure_not_flaky():
    runs = _load_runs()
    flaky = detect_flaky(runs)
    names = [f.name for f in flaky]
    # test_login_invalid fails in every run — should not appear as flaky
    assert "tests/test_login.py::test_login_invalid" not in names


def test_deterministic_pass_not_flaky():
    runs = _load_runs()
    flaky = detect_flaky(runs)
    names = [f.name for f in flaky]
    assert "tests/test_login.py::test_login_success" not in names


def test_flakiness_score_50_50():
    from slog.models import FlakyTest
    f = FlakyTest(name="x", total_runs=2, pass_count=1, fail_count=1)
    assert f.flakiness_score == pytest.approx(1.0)


def test_flakiness_score_deterministic():
    from slog.models import FlakyTest
    f = FlakyTest(name="x", total_runs=3, pass_count=3, fail_count=0)
    assert f.flakiness_score == pytest.approx(0.0)
