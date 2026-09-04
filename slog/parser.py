from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from .models import TestResult, TestRun


def parse_report(path: Union[str, Path]) -> TestRun:
    path = Path(path)
    data = json.loads(path.read_text())

    created = data.get("created", 0)
    timestamp = datetime.fromtimestamp(created, tz=timezone.utc)

    environment = data.get("environment", {}).get("Platform", "unknown")

    results: list[TestResult] = []
    for test in data.get("tests", []):
        call = test.get("call", {})
        setup = test.get("setup", {})
        teardown = test.get("teardown", {})

        # prefer call phase for failure info
        for phase in (call, setup, teardown):
            longrepr = phase.get("longrepr", "")
            if longrepr:
                break

        error_message = None
        stacktrace = None
        if longrepr:
            lines = longrepr.splitlines()
            # last line is usually the short assertion message
            error_message = lines[-1].strip() if lines else longrepr
            stacktrace = longrepr

        screenshot = test.get("user_properties", {})
        if isinstance(screenshot, list):
            screenshot = dict(screenshot)
        screenshot_path = screenshot.get("screenshot")

        retries = test.get("retries", 0)

        results.append(
            TestResult(
                name=test["nodeid"],
                status=test["outcome"],
                duration=test.get("call", {}).get("duration", 0.0),
                error_message=error_message,
                stacktrace=stacktrace,
                screenshot_path=screenshot_path,
                retries=retries,
            )
        )

    return TestRun(
        timestamp=timestamp,
        environment=environment,
        results=results,
        source_file=str(path),
    )
