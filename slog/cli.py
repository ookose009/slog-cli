from __future__ import annotations

import glob
import sys
from pathlib import Path

import click
from rich.console import Console

from .aggregator import cluster_failures, detect_flaky
from .parser import parse_report
from .report import print_summary, render_html
from .runner import run_suite

console = Console()


@click.group()
def main() -> None:
    """slog — Selenium test log analyzer."""


@main.command()
@click.argument("test_path")
@click.option("--retries", default=0, show_default=True, help="Rerun failing tests N times.")
def run(test_path: str, retries: int) -> None:
    """Run pytest against TEST_PATH and save a timestamped report."""
    console.print(f"[bold]Running[/bold] {test_path} (retries={retries})")
    run_dir = run_suite(test_path, retries=retries)
    console.print(f"[green]Artifacts saved to[/green] {run_dir}")

    json_report = run_dir / "report.json"
    if json_report.exists():
        run = parse_report(json_report)
        console.print(
            f"Results: [green]{len(run.passed)} passed[/green], "
            f"[red]{len(run.failed)} failed[/red] / {len(run.results)} total"
        )


@main.command()
@click.argument("paths", nargs=-1, required=True)
def analyze(paths: tuple[str, ...]) -> None:
    """Parse one or more JSON reports and print cluster + flakiness tables."""
    report_files = _expand_paths(paths)
    if not report_files:
        console.print("[red]No report files found.[/red]")
        sys.exit(1)

    runs = [parse_report(p) for p in report_files]
    clusters = cluster_failures(runs)
    flaky = detect_flaky(runs)
    print_summary(runs, clusters, flaky)


@main.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--format", "fmt", default="html", type=click.Choice(["html"]), show_default=True)
@click.option("--output", default="slog-report.html", show_default=True)
def report(paths: tuple[str, ...], fmt: str, output: str) -> None:
    """Generate a static HTML report from one or more JSON run reports."""
    report_files = _expand_paths(paths)
    if not report_files:
        console.print("[red]No report files found.[/red]")
        sys.exit(1)

    runs = [parse_report(p) for p in report_files]
    clusters = cluster_failures(runs)
    flaky = detect_flaky(runs)

    out = Path(output)
    render_html(runs, clusters, flaky, out)
    console.print(f"[green]Report written to[/green] {out.resolve()}")


def _expand_paths(paths: tuple[str, ...]) -> list[Path]:
    result: list[Path] = []
    for pattern in paths:
        matched = glob.glob(pattern, recursive=True)
        if matched:
            result.extend(Path(p) for p in matched)
        else:
            p = Path(pattern)
            if p.exists():
                result.append(p)
    return sorted(set(result))
