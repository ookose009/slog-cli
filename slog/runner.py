from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_suite(test_path: str, retries: int = 0, base_dir: Path = Path(".slog")) -> Path:
    """Run pytest against test_path and save artifacts under .slog/runs/<timestamp>/."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = base_dir / "runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    json_report = run_dir / "report.json"
    html_report = run_dir / "report.html"

    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        f"--json-report", f"--json-report-file={json_report}",
        f"--html={html_report}", "--self-contained-html",
    ]
    if retries > 0:
        cmd += [f"--reruns={retries}"]

    result = subprocess.run(cmd, capture_output=False)

    return run_dir
