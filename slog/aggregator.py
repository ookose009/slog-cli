from __future__ import annotations

from collections import defaultdict
from typing import List

from .models import FailureCluster, FlakyTest, TestResult, TestRun


def cluster_failures(runs: List[TestRun]) -> List[FailureCluster]:
    """Group failures across runs by normalized stack-trace signature."""
    sig_map: dict[str, FailureCluster] = {}

    for run in runs:
        for result in run.failed:
            sig = result.normalized_error or result.error_message or "unknown"
            # use first 300 chars as key so near-identical traces cluster
            key = sig[:300]
            if key not in sig_map:
                sig_map[key] = FailureCluster(
                    signature=key,
                    likely_cause=result.likely_cause,
                )
            sig_map[key].occurrences += 1
            if result.name not in sig_map[key].test_names:
                sig_map[key].test_names.append(result.name)

    return sorted(sig_map.values(), key=lambda c: c.occurrences, reverse=True)


def detect_flaky(runs: List[TestRun]) -> List[FlakyTest]:
    """Find tests that both pass and fail across runs."""
    pass_counts: dict[str, int] = defaultdict(int)
    fail_counts: dict[str, int] = defaultdict(int)
    total_counts: dict[str, int] = defaultdict(int)

    for run in runs:
        for result in run.results:
            total_counts[result.name] += 1
            if result.status == "passed":
                pass_counts[result.name] += 1
            elif result.status in ("failed", "error"):
                fail_counts[result.name] += 1

    flaky: list[FlakyTest] = []
    for name, total in total_counts.items():
        passes = pass_counts[name]
        fails = fail_counts[name]
        if passes > 0 and fails > 0:
            ft = FlakyTest(
                name=name,
                total_runs=total,
                pass_count=passes,
                fail_count=fails,
            )
            flaky.append(ft)

    return sorted(flaky, key=lambda f: f.flakiness_score, reverse=True)
