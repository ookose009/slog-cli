# slog — Selenium Test Log Analyzer

A pip-installable CLI that runs Selenium/pytest UI test suites and automatically
analyzes results: clustering failures by root cause, detecting flaky tests across
multiple runs, and generating shareable HTML reports.

## Installation

```bash
# Core tool (no browser driver required)
pip install -e .

# With Selenium support for running suites
pip install -e ".[selenium]"

# With dev/test dependencies
pip install -e ".[selenium,dev]"
```

## Usage

### Run a test suite

```bash
slog run examples/sample_selenium_suite/ --retries 2
```

Runs pytest, saves a timestamped JSON + HTML report under `.slog/runs/<timestamp>/`.

### Analyze past runs

```bash
slog analyze .slog/runs/*/report.json
```

Prints failure clusters and flaky test tables to the terminal.

### Generate an HTML report

```bash
slog report .slog/runs/*/report.json --output report.html
```

Produces a static, self-contained HTML file you can share with your team.

## How it works

| Concept | Description |
|---|---|
| **Failure cluster** | Failures with the same normalized stack trace (file paths and line numbers stripped) are grouped together. |
| **Flakiness score** | 0.0 = deterministically passes or fails; approaches 1.0 as the pass/fail ratio nears 50/50. |
| **Likely cause** | Heuristic: `TimeoutException` / `StaleElementReferenceException` → `likely_flaky`; `AssertionError` / `NoSuchElementException` → `likely_regression`. |

## Running the unit tests

```bash
pytest tests/
```

No browser required — unit tests use fixture JSON files in `tests/fixtures/`.

## Demo suite

`examples/sample_selenium_suite/` runs against [the-internet.herokuapp.com](https://the-internet.herokuapp.com).
Requires Chrome and the `[selenium]` extras. Includes one intentionally
timing-sensitive test to demonstrate flakiness detection.

## Project layout

```
slog/
├── cli.py          # click entrypoint
├── runner.py       # invokes pytest as subprocess
├── parser.py       # parses pytest-json-report JSON
├── aggregator.py   # clusters failures, computes flakiness scores
├── report.py       # rich terminal tables + HTML renderer
└── models.py       # TestResult, TestRun, FailureCluster, FlakyTest
tests/
├── test_parser.py
├── test_aggregator.py
└── fixtures/       # sample multi-run JSON reports
examples/
└── sample_selenium_suite/
```
