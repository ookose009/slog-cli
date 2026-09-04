from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class TestResult:
    name: str
    status: str  # "passed" | "failed" | "error" | "skipped"
    duration: float
    error_message: Optional[str] = None
    stacktrace: Optional[str] = None
    screenshot_path: Optional[str] = None
    retries: int = 0

    @property
    def normalized_error(self) -> str:
        if not self.stacktrace:
            return self.error_message or ""
        text = self.stacktrace
        # strip file paths and line numbers
        text = re.sub(r'File "[^"]+", line \d+', 'File "<path>", line N', text)
        # strip memory addresses
        text = re.sub(r'0x[0-9a-fA-F]+', '0x...', text)
        # strip timestamps / UUIDs
        text = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<uuid>', text)
        # collapse varying element IDs
        text = re.sub(r'element-\d+', 'element-N', text)
        return text.strip()

    @property
    def likely_cause(self) -> str:
        flaky_patterns = [
            "TimeoutException",
            "StaleElementReferenceException",
            "ElementClickInterceptedException",
            "WebDriverException",
            "NoSuchWindowException",
        ]
        regression_patterns = [
            "AssertionError",
            "NoSuchElementException",
            "ElementNotInteractableException",
        ]
        combined = (self.error_message or "") + (self.stacktrace or "")
        for p in flaky_patterns:
            if p in combined:
                return "likely_flaky"
        for p in regression_patterns:
            if p in combined:
                return "likely_regression"
        return "unknown"


@dataclass
class TestRun:
    timestamp: datetime
    environment: str
    results: List[TestResult] = field(default_factory=list)
    source_file: Optional[str] = None

    @property
    def passed(self) -> List[TestResult]:
        return [r for r in self.results if r.status == "passed"]

    @property
    def failed(self) -> List[TestResult]:
        return [r for r in self.results if r.status in ("failed", "error")]

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return len(self.passed) / len(self.results)


@dataclass
class FailureCluster:
    signature: str
    likely_cause: str
    occurrences: int = 0
    test_names: List[str] = field(default_factory=list)


@dataclass
class FlakyTest:
    name: str
    total_runs: int
    pass_count: int
    fail_count: int

    @property
    def flakiness_score(self) -> float:
        """0.0 = deterministic; approaches 1.0 as pass/fail split nears 50/50."""
        if self.total_runs == 0:
            return 0.0
        ratio = self.pass_count / self.total_runs
        # 1 - |2r - 1|  peaks at 1.0 when ratio=0.5, zero at 0 or 1
        return 1.0 - abs(2 * ratio - 1)
