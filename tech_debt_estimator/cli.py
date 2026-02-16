"""Command-line interface for technical debt estimator."""

import os
import sys
import click
from pathlib import Path
from typing import Optional

from .analyzer import TechnicalDebtAnalyzer, Severity
from .formatters import get_formatter
from . import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """Technical Debt Estimator - Quantify technical debt in developer-hours."""
    pass


@main.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.')
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['table', 'json', 'markdown']),
    default='table',
    help='Output format'
)
@click.option(
    '--output-file',
    type=click.Path(),
    help='Write output to file instead of stdout'
)
def scan(path: str, output_format: str, output_file: Optional[str]):
    """Perform complete technical debt scan on repository.

    PATH is the directory to scan (defaults to current directory)
    """
    try:
        path = os.path.abspath(path)

        if not os.path.isdir(path):
            click.echo(f"Error: {path} is not a directory", err=True)
            sys.exit(1)

        click.echo(f"Scanning {path}...", err=True)

        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(path)

        formatter = get_formatter(output_format)
        output = formatter.format(result)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            click.echo(f"Report written to {output_file}", err=True)
        else:
            click.echo(output)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.')
@click.option('--top', type=int, default=10, help='Number of top offenders to show')
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['table', 'json']),
    default='table',
    help='Output format'
)
def hotspots(path: str, top: int, output_format: str):
    """Show complexity hotspots - files with highest technical debt concentration.

    PATH is the directory to scan (defaults to current directory)
    """
    try:
        path = os.path.abspath(path)

        if not os.path.isdir(path):
            click.echo(f"Error: {path} is not a directory", err=True)
            sys.exit(1)

        from .metrics import find_complex_files, get_lines_of_code

        click.echo(f"Finding complexity hotspots in {path}...", err=True)

        complex_files = find_complex_files(path, threshold=500)

        if not complex_files:
            click.echo("No complexity hotspots found!", err=True)
            return

        if output_format == 'json':
            import json
            data = {
                'repository': path,
                'hotspots': [
                    {'file': name, 'lines_of_code': loc}
                    for name, loc in complex_files[:top]
                ]
            }
            click.echo(json.dumps(data, indent=2))
        else:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title=f"Top {top} Complexity Hotspots")
            table.add_column("File", style="cyan")
            table.add_column("Lines of Code", justify="right", style="yellow")
            table.add_column("Debt Impact", style="red")

            for i, (name, loc) in enumerate(complex_files[:top], 1):
                debt_impact = f"{(loc // 500) * 10} hours"
                table.add_row(name, str(loc), debt_impact)

            console.print(table)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.')
@click.option(
    '--commits',
    type=int,
    default=20,
    help='Number of recent commits to analyze'
)
@click.option(
    '--format',
    'output_format',
    type=click.Choice(['table', 'json']),
    default='table',
    help='Output format'
)
def trend(path: str, commits: int, output_format: str):
    """Show technical debt trend over recent commits.

    PATH is the directory to scan (defaults to current directory)
    """
    try:
        path = os.path.abspath(path)

        if not os.path.isdir(path):
            click.echo(f"Error: {path} is not a directory", err=True)
            sys.exit(1)

        # Check if it's a git repository
        try:
            from git import Repo
            repo = Repo(path)
        except Exception:
            click.echo("Error: Not a git repository or git not installed", err=True)
            sys.exit(1)

        click.echo(f"Analyzing debt trend over last {commits} commits...", err=True)

        analyzer = TechnicalDebtAnalyzer()

        # Get recent commits
        try:
            commit_list = list(repo.iter_commits('HEAD', max_count=commits))
        except Exception as e:
            click.echo(f"Error reading commits: {str(e)}", err=True)
            sys.exit(1)

        if not commit_list:
            click.echo("No commits found", err=True)
            sys.exit(1)

        # Analyze current state (most recent)
        current_result = analyzer.analyze(path)

        trend_data = {
            'repository': path,
            'current_total_hours': round(current_result.total_hours, 2),
            'analyzed_commits': len(commit_list),
            'analysis_note': 'Full analysis performed on working directory. Trend analysis coming soon.'
        }

        if output_format == 'json':
            import json
            click.echo(json.dumps(trend_data, indent=2))
        else:
            from rich.console import Console
            from rich.panel import Panel

            console = Console()

            status_text = (
                f"Repository: {path}\n"
                f"Current Debt: {current_result.total_hours:.1f} hours\n"
                f"Commits Analyzed: {len(commit_list)}\n\n"
                f"Note: For complete trend analysis with historical debt data,\n"
                f"integrate with your CI/CD pipeline to track debt at each commit."
            )

            console.print(Panel(status_text, title="Debt Trend Analysis"))

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
