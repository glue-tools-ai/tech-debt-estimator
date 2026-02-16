"""Output formatters for technical debt reports."""

import json
from typing import Dict, Any
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .analyzer import DebtResult, DebtCategory, Severity


class BaseFormatter:
    """Base formatter class."""

    def format(self, result: DebtResult) -> str:
        """Format the result. Must be implemented by subclasses."""
        raise NotImplementedError


class TableFormatter(BaseFormatter):
    """Format results as Rich console table."""

    def format(self, result: DebtResult) -> str:
        """Format as colored table with Rich."""
        console = Console()

        # Title
        title = f"TECHNICAL DEBT ANALYSIS\nRepository: {result.repo_path}"
        console.print(Panel(title, style="bold blue"))

        # Main table
        table = Table(title="DEBT CATEGORIES", show_header=True, header_style="bold")
        table.add_column("Category", style="cyan", width=25)
        table.add_column("Hours", justify="right", width=10)
        table.add_column("Severity", width=12)
        table.add_column("Top Affected Files", width=40)

        for category_name, category in result.sorted_categories():
            severity_text = f"{category.severity.emoji} {category.severity.name}"
            severity_style = category.severity.color

            # Format affected files
            files_text = "\n".join(category.affected_files[:3])
            if len(category.affected_files) > 3:
                files_text += f"\n... and {len(category.affected_files) - 3} more"

            table.add_row(
                category_name,
                f"{category.estimated_hours:.1f}",
                Text(severity_text, style=severity_style),
                files_text
            )

        console.print(table)

        # Summary panel
        summary_text = f"[bold]Total Estimated Debt:[/bold] {result.total_hours:.1f} developer-hours\n"
        summary_text += f"[bold]Analysis Date:[/bold] {result.analyzed_at}\n"

        critical = sum(1 for c in result.categories.values() if c.severity == Severity.CRITICAL)
        high = sum(1 for c in result.categories.values() if c.severity == Severity.HIGH)

        if critical > 0:
            summary_text += f"[bold red]{critical} CRITICAL areas[/bold red]\n"
        if high > 0:
            summary_text += f"[bold yellow]{high} HIGH priority areas[/bold yellow]"

        console.print(Panel(summary_text, style="bold green", title="SUMMARY"))

        # Recommendations
        console.print("\n[bold]RECOMMENDATIONS[/bold]")
        rec_table = Table(show_header=False, show_lines=False)
        rec_table.add_column("", style="dim", width=2)
        rec_table.add_column("", width=70)

        recs_shown = set()
        for category_name, category in result.sorted_categories():
            for rec in category.recommendations[:1]:  # Show top recommendation per category
                if rec not in recs_shown:
                    rec_table.add_row("•", rec)
                    recs_shown.add(rec)

        console.print(rec_table)

        # Capture output
        from io import StringIO
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)

        # Re-create output in string buffer
        table = Table(title="DEBT CATEGORIES", show_header=True, header_style="bold")
        table.add_column("Category", style="cyan", width=25)
        table.add_column("Hours", justify="right", width=10)
        table.add_column("Severity", width=12)
        table.add_column("Top Affected Files", width=40)

        for category_name, category in result.sorted_categories():
            severity_text = f"{category.severity.emoji} {category.severity.name}"
            severity_style = category.severity.color

            files_text = "\n".join(category.affected_files[:3])
            if len(category.affected_files) > 3:
                files_text += f"\n... and {len(category.affected_files) - 3} more"

            table.add_row(
                category_name,
                f"{category.estimated_hours:.1f}",
                Text(severity_text, style=severity_style),
                files_text
            )

        console.print(table)
        console.print(Panel(summary_text, style="bold green", title="SUMMARY"))

        return string_io.getvalue()


class JSONFormatter(BaseFormatter):
    """Format results as JSON."""

    def format(self, result: DebtResult) -> str:
        """Format as JSON."""
        data = {
            "repository": result.repo_path,
            "analyzed_at": result.analyzed_at,
            "total_hours": round(result.total_hours, 2),
            "summary": result.summary,
            "categories": self._format_categories(result.categories)
        }
        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def _format_categories(categories: Dict[str, DebtCategory]) -> Dict[str, Any]:
        """Format categories for JSON."""
        formatted = {}
        for name, category in categories.items():
            formatted[name] = {
                "estimated_hours": round(category.estimated_hours, 2),
                "severity": category.severity.name,
                "affected_files": category.affected_files,
                "recommendations": category.recommendations,
                "details": category.details
            }
        return formatted


class MarkdownFormatter(BaseFormatter):
    """Format results as Markdown."""

    def format(self, result: DebtResult) -> str:
        """Format as Markdown."""
        lines = []

        lines.append("# Technical Debt Analysis Report\n")
        lines.append(f"**Repository:** `{result.repo_path}`\n")
        lines.append(f"**Analysis Date:** {result.analyzed_at}\n")
        lines.append(f"**Total Estimated Debt:** {result.total_hours:.1f} developer-hours\n")

        lines.append("\n## Summary\n")
        lines.append(result.summary + "\n")

        lines.append("\n## Debt Categories\n")
        lines.append("| Category | Hours | Severity | Files |")
        lines.append("|----------|-------|----------|-------|")

        for category_name, category in result.sorted_categories():
            files_str = ", ".join(category.affected_files[:3])
            if len(category.affected_files) > 3:
                files_str += f", ... +{len(category.affected_files) - 3} more"

            lines.append(
                f"| {category_name} | {category.estimated_hours:.1f} | "
                f"{category.severity.emoji} {category.severity.name} | {files_str} |"
            )

        lines.append("\n## Detailed Findings\n")

        for category_name, category in result.sorted_categories():
            lines.append(f"\n### {category_name}\n")
            lines.append(f"- **Severity:** {category.severity.emoji} {category.severity.name}\n")
            lines.append(f"- **Estimated Hours:** {category.estimated_hours:.1f}\n")
            lines.append("- **Affected Files:**\n")

            for f in category.affected_files[:5]:
                lines.append(f"  - {f}\n")

            lines.append("- **Recommendations:**\n")
            for rec in category.recommendations:
                lines.append(f"  1. {rec}\n")

        lines.append("\n---\n")
        lines.append("*Report generated by tech-debt-estimator*\n")

        return "".join(lines)


def get_formatter(format_type: str) -> BaseFormatter:
    """Get formatter instance by type."""
    formatters = {
        'table': TableFormatter,
        'json': JSONFormatter,
        'markdown': MarkdownFormatter,
    }

    formatter_class = formatters.get(format_type, TableFormatter)
    return formatter_class()
