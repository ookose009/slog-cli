from __future__ import annotations

from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table

from .models import FailureCluster, FlakyTest, TestRun

console = Console()

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>slog report</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; color: #1a1a1a; }}
  h1 {{ color: #2563eb; }}
  h2 {{ border-bottom: 2px solid #e5e7eb; padding-bottom: .25rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
  th {{ background: #f3f4f6; text-align: left; padding: .5rem .75rem; }}
  td {{ padding: .5rem .75rem; border-bottom: 1px solid #e5e7eb; }}
  .flaky {{ color: #d97706; font-weight: 600; }}
  .regression {{ color: #dc2626; font-weight: 600; }}
  .unknown {{ color: #6b7280; }}
  .badge {{ display: inline-block; border-radius: 999px; padding: .1rem .6rem; font-size: .8rem; }}
  .badge-pass {{ background: #d1fae5; color: #065f46; }}
  .badge-fail {{ background: #fee2e2; color: #991b1b; }}
  pre {{ background: #f9fafb; border: 1px solid #e5e7eb; padding: 1rem; border-radius: .375rem;
         overflow-x: auto; font-size: .8rem; white-space: pre-wrap; word-break: break-all; }}
</style>
</head>
<body>
<h1>slog — Test Analysis Report</h1>
<p><em>Runs analysed: {run_count}</em></p>

<h2>Failure Clusters</h2>
{clusters_table}

<h2>Flaky Tests</h2>
{flaky_table}

<h2>Run Summary</h2>
{runs_table}
</body>
</html>
"""


def _cluster_row(c: FailureCluster) -> str:
    cause_cls = "flaky" if "flaky" in c.likely_cause else ("regression" if "regression" in c.likely_cause else "unknown")
    names = "<br>".join(c.test_names)
    sig = c.signature[:300].replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"<tr><td>{c.occurrences}</td>"
        f"<td class='{cause_cls}'>{c.likely_cause}</td>"
        f"<td>{names}</td>"
        f"<td><pre>{sig}</pre></td></tr>"
    )


def _flaky_row(f: FlakyTest) -> str:
    score_pct = f"{f.flakiness_score * 100:.0f}%"
    return (
        f"<tr><td>{f.name}</td>"
        f"<td>{f.total_runs}</td>"
        f"<td><span class='badge badge-pass'>{f.pass_count} pass</span></td>"
        f"<td><span class='badge badge-fail'>{f.fail_count} fail</span></td>"
        f"<td><strong>{score_pct}</strong></td></tr>"
    )


def _run_row(run: TestRun) -> str:
    ts = run.timestamp.strftime("%Y-%m-%d %H:%M UTC")
    pct = f"{run.pass_rate * 100:.0f}%"
    return (
        f"<tr><td>{ts}</td>"
        f"<td>{run.environment}</td>"
        f"<td>{len(run.results)}</td>"
        f"<td>{len(run.passed)}</td>"
        f"<td>{len(run.failed)}</td>"
        f"<td>{pct}</td></tr>"
    )


def _html_table(headers: list[str], rows: list[str]) -> str:
    if not rows:
        return "<p><em>None.</em></p>"
    ths = "".join(f"<th>{h}</th>" for h in headers)
    return f"<table><thead><tr>{ths}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def render_html(
    runs: List[TestRun],
    clusters: List[FailureCluster],
    flaky: List[FlakyTest],
    output: Path,
) -> None:
    clusters_table = _html_table(
        ["Occurrences", "Cause", "Tests", "Signature"],
        [_cluster_row(c) for c in clusters],
    )
    flaky_table = _html_table(
        ["Test", "Total Runs", "Passes", "Fails", "Flakiness"],
        [_flaky_row(f) for f in flaky],
    )
    runs_table = _html_table(
        ["Timestamp", "Environment", "Total", "Passed", "Failed", "Pass Rate"],
        [_run_row(r) for r in runs],
    )
    html = _HTML_TEMPLATE.format(
        run_count=len(runs),
        clusters_table=clusters_table,
        flaky_table=flaky_table,
        runs_table=runs_table,
    )
    output.write_text(html)


def print_summary(runs: List[TestRun], clusters: List[FailureCluster], flaky: List[FlakyTest]) -> None:
    console.rule("[bold blue]slog — Analysis Summary[/bold blue]")

    # Run overview
    run_table = Table(title="Runs", show_lines=False)
    run_table.add_column("Timestamp", style="dim")
    run_table.add_column("Tests")
    run_table.add_column("Passed", style="green")
    run_table.add_column("Failed", style="red")
    run_table.add_column("Pass Rate")
    for run in runs:
        run_table.add_row(
            run.timestamp.strftime("%Y-%m-%d %H:%M UTC"),
            str(len(run.results)),
            str(len(run.passed)),
            str(len(run.failed)),
            f"{run.pass_rate * 100:.0f}%",
        )
    console.print(run_table)

    # Failure clusters
    if clusters:
        cl_table = Table(title="Failure Clusters", show_lines=True)
        cl_table.add_column("Occurrences", justify="right")
        cl_table.add_column("Cause")
        cl_table.add_column("Tests")
        cl_table.add_column("Signature", no_wrap=False, max_width=60)
        for c in clusters:
            cl_table.add_row(
                str(c.occurrences),
                c.likely_cause,
                "\n".join(c.test_names),
                c.signature[:200],
            )
        console.print(cl_table)

    # Flaky tests
    if flaky:
        fl_table = Table(title="Flaky Tests", show_lines=False)
        fl_table.add_column("Test")
        fl_table.add_column("Runs", justify="right")
        fl_table.add_column("Pass", style="green", justify="right")
        fl_table.add_column("Fail", style="red", justify="right")
        fl_table.add_column("Flakiness", justify="right")
        for f in flaky:
            fl_table.add_row(
                f.name,
                str(f.total_runs),
                str(f.pass_count),
                str(f.fail_count),
                f"{f.flakiness_score * 100:.0f}%",
            )
        console.print(fl_table)
    else:
        console.print("[green]No flaky tests detected.[/green]")
