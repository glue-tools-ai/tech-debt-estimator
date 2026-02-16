"""Technical debt analysis engine."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum

from .metrics import (
    find_complex_files,
    find_duplicate_blocks,
    find_stale_files,
    find_untested_code,
    find_undocumented_code,
    analyze_dependency_age,
)


class Severity(Enum):
    """Debt severity levels."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1

    @property
    def color(self) -> str:
        """Get color for severity level."""
        return {
            Severity.CRITICAL: "red",
            Severity.HIGH: "yellow",
            Severity.MEDIUM: "cyan",
            Severity.LOW: "green"
        }[self]

    @property
    def emoji(self) -> str:
        """Get emoji for severity level."""
        return {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🟢"
        }[self]


@dataclass
class DebtCategory:
    """Represents a technical debt category."""
    name: str
    estimated_hours: float
    severity: Severity
    affected_files: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


@dataclass
class DebtResult:
    """Complete technical debt analysis result."""
    repo_path: str
    total_hours: float
    categories: Dict[str, DebtCategory]
    analyzed_at: str
    summary: str = ""

    def sorted_categories(self) -> List[Tuple[str, DebtCategory]]:
        """Get categories sorted by severity and hours."""
        return sorted(
            self.categories.items(),
            key=lambda x: (x[1].severity.value, x[1].estimated_hours),
            reverse=True
        )


class TechnicalDebtAnalyzer:
    """Analyzes technical debt in a codebase."""

    # Estimation parameters (in hours)
    REFACTOR_HOURS_PER_FILE = 10
    DUP_HOURS_PER_BLOCK = 3
    TEST_HOURS_PER_FILE = 4
    DOC_HOURS_PER_ITEM = 0.5
    STALE_HOURS_PER_FILE = 6
    DEPENDENCY_BASE_HOURS = 5

    # Thresholds
    COMPLEXITY_THRESHOLD = 500  # lines of code
    STALE_MONTHS = 12

    def analyze(self, repo_path: str) -> DebtResult:
        """Perform complete technical debt analysis."""
        repo_path = os.path.abspath(repo_path)

        categories = {
            'Complexity Debt': self._analyze_complexity(repo_path),
            'Duplication Debt': self._analyze_duplication(repo_path),
            'Test Coverage Debt': self._analyze_tests(repo_path),
            'Documentation Debt': self._analyze_documentation(repo_path),
            'Stale Code Debt': self._analyze_stale_code(repo_path),
            'Dependency Debt': self._analyze_dependencies(repo_path),
        }

        total_hours = sum(cat.estimated_hours for cat in categories.values())

        result = DebtResult(
            repo_path=repo_path,
            total_hours=total_hours,
            categories=categories,
            analyzed_at=self._get_timestamp(),
            summary=self._generate_summary(categories, total_hours)
        )

        return result

    def _analyze_complexity(self, repo_path: str) -> DebtCategory:
        """Analyze code complexity debt."""
        complex_files = find_complex_files(repo_path, self.COMPLEXITY_THRESHOLD)

        affected_files = [f"{name} ({loc} lines)" for name, loc in complex_files[:10]]
        estimated_hours = len(complex_files) * self.REFACTOR_HOURS_PER_FILE

        # Determine severity based on count
        if len(complex_files) > 20:
            severity = Severity.CRITICAL
        elif len(complex_files) > 10:
            severity = Severity.HIGH
        elif len(complex_files) > 5:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        recommendations = [
            f"Refactor {len(complex_files)} overly complex files (>500 LOC)",
            "Break down large functions into smaller units",
            "Extract utility functions and helper methods",
            "Consider splitting large modules into submodules"
        ]

        return DebtCategory(
            name="Complexity Debt",
            estimated_hours=estimated_hours,
            severity=severity,
            affected_files=affected_files,
            recommendations=recommendations,
            details={'file_count': len(complex_files)}
        )

    def _analyze_duplication(self, repo_path: str) -> DebtCategory:
        """Analyze code duplication debt."""
        duplicates = find_duplicate_blocks(repo_path)

        duplicate_count = len(duplicates)
        total_blocks = sum(d['count'] for d in duplicates)
        estimated_hours = duplicate_count * self.DUP_HOURS_PER_BLOCK

        affected_files = []
        for dup in duplicates[:5]:
            files = set(loc[0] for loc in dup['locations'])
            affected_files.append(f"{len(files)} files ({dup['count']} occurrences)")

        # Determine severity
        if duplicate_count > 30:
            severity = Severity.CRITICAL
        elif duplicate_count > 15:
            severity = Severity.HIGH
        elif duplicate_count > 5:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        recommendations = [
            f"Extract {duplicate_count} duplicated code blocks into shared utilities",
            "Implement DRY principle across codebase",
            "Use code generation or templates where applicable",
            "Regular duplication scanning in CI/CD"
        ]

        return DebtCategory(
            name="Duplication Debt",
            estimated_hours=estimated_hours,
            severity=severity,
            affected_files=affected_files[:5],
            recommendations=recommendations,
            details={'duplicate_blocks': duplicate_count, 'total_occurrences': total_blocks}
        )

    def _analyze_tests(self, repo_path: str) -> DebtCategory:
        """Analyze test coverage debt."""
        untested_files = find_untested_code(repo_path)

        estimated_hours = len(untested_files) * self.TEST_HOURS_PER_FILE

        affected_files = untested_files[:10]

        # Determine severity
        if len(untested_files) > 50:
            severity = Severity.CRITICAL
        elif len(untested_files) > 25:
            severity = Severity.HIGH
        elif len(untested_files) > 10:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        recommendations = [
            f"Add tests for {len(untested_files)} untested source files",
            "Set minimum code coverage threshold (80%+)",
            "Implement test-driven development practices",
            "Add pre-commit hooks to check test coverage"
        ]

        return DebtCategory(
            name="Test Coverage Debt",
            estimated_hours=estimated_hours,
            severity=severity,
            affected_files=affected_files,
            recommendations=recommendations,
            details={'untested_files': len(untested_files)}
        )

    def _analyze_documentation(self, repo_path: str) -> DebtCategory:
        """Analyze documentation debt."""
        undocumented = find_undocumented_code(repo_path)

        total_undocumented = sum(len(items) for items in undocumented.values())
        estimated_hours = total_undocumented * self.DOC_HOURS_PER_ITEM

        affected_files = []
        for filepath, items in list(undocumented.items())[:5]:
            affected_files.append(f"{filepath} ({len(items)} undocumented)")

        # Determine severity
        if total_undocumented > 100:
            severity = Severity.CRITICAL
        elif total_undocumented > 50:
            severity = Severity.HIGH
        elif total_undocumented > 20:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        recommendations = [
            f"Add docstrings to {total_undocumented} functions/classes",
            "Document public API endpoints",
            "Create architecture decision records (ADRs)",
            "Enforce documentation in code review process"
        ]

        return DebtCategory(
            name="Documentation Debt",
            estimated_hours=estimated_hours,
            severity=severity,
            affected_files=affected_files,
            recommendations=recommendations,
            details={'undocumented_count': total_undocumented}
        )

    def _analyze_stale_code(self, repo_path: str) -> DebtCategory:
        """Analyze stale/dead code debt."""
        stale_files = find_stale_files(repo_path, self.STALE_MONTHS)

        estimated_hours = len(stale_files) * self.STALE_HOURS_PER_FILE

        affected_files = [f"{name} (last: {date})" for name, date in stale_files[:10]]

        # Determine severity
        if len(stale_files) > 30:
            severity = Severity.CRITICAL
        elif len(stale_files) > 15:
            severity = Severity.HIGH
        elif len(stale_files) > 5:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        recommendations = [
            f"Audit {len(stale_files)} stale code files",
            "Remove or archive dead code branches",
            "Consolidate overlapping functionality",
            "Establish code maintenance policy"
        ]

        return DebtCategory(
            name="Stale Code Debt",
            estimated_hours=estimated_hours,
            severity=severity,
            affected_files=affected_files,
            recommendations=recommendations,
            details={'stale_files': len(stale_files)}
        )

    def _analyze_dependencies(self, repo_path: str) -> DebtCategory:
        """Analyze dependency debt."""
        dep_analysis = analyze_dependency_age(repo_path)

        estimated_hours = self.DEPENDENCY_BASE_HOURS

        affected_files = []
        if dep_analysis['has_requirements']:
            affected_files.append("requirements.txt / setup.py / pyproject.toml")
        if dep_analysis['has_lock_file']:
            age_days = dep_analysis['lock_file_age_days'] or 0
            affected_files.append(f"Lock files ({age_days} days old)")

        # Determine severity based on lock file age
        if dep_analysis['lock_file_age_days'] and dep_analysis['lock_file_age_days'] > 180:
            severity = Severity.HIGH
        elif dep_analysis['lock_file_age_days'] and dep_analysis['lock_file_age_days'] > 90:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        # Increase severity if missing files
        if not dep_analysis['has_requirements']:
            severity = Severity.CRITICAL
            estimated_hours += 3

        recommendations = [
            "Update all dependencies to latest stable versions",
            "Implement dependency audit process",
            "Use tools like Dependabot for automated updates",
            "Document breaking changes during dependency upgrades"
        ]

        return DebtCategory(
            name="Dependency Debt",
            estimated_hours=estimated_hours,
            severity=severity,
            affected_files=affected_files,
            recommendations=recommendations,
            details=dep_analysis
        )

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    @staticmethod
    def _generate_summary(categories: Dict[str, DebtCategory], total_hours: float) -> str:
        """Generate summary text."""
        critical_count = sum(1 for cat in categories.values() if cat.severity == Severity.CRITICAL)
        high_count = sum(1 for cat in categories.values() if cat.severity == Severity.HIGH)

        summary = f"Total technical debt: {total_hours:.1f} developer-hours"
        if critical_count > 0:
            summary += f" ({critical_count} CRITICAL areas)"
        if high_count > 0:
            summary += f" ({high_count} HIGH areas)"

        return summary
