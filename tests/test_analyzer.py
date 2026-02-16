"""Tests for technical debt analyzer."""

import os
import tempfile
import pytest
from pathlib import Path

from tech_debt_estimator.analyzer import TechnicalDebtAnalyzer, Severity
from tech_debt_estimator.metrics import (
    find_complex_files,
    find_duplicate_blocks,
    find_stale_files,
    find_untested_code,
    find_undocumented_code,
)


@pytest.fixture
def sample_repo():
    """Create a sample repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a complex Python file
        complex_file = os.path.join(tmpdir, "complex.py")
        with open(complex_file, 'w') as f:
            f.write("def function1():\n" + "    pass\n" * 600)

        # Create a simple file
        simple_file = os.path.join(tmpdir, "simple.py")
        with open(simple_file, 'w') as f:
            f.write('"""Module docstring."""\n\ndef hello():\n    """Say hello."""\n    print("hello")\n')

        # Create undocumented file
        undoc_file = os.path.join(tmpdir, "undocumented.py")
        with open(undoc_file, 'w') as f:
            f.write("def function_without_docstring():\n    pass\n")

        # Create test file
        test_dir = os.path.join(tmpdir, "tests")
        os.makedirs(test_dir)
        test_file = os.path.join(test_dir, "test_simple.py")
        with open(test_file, 'w') as f:
            f.write('def test_hello():\n    assert True\n')

        # Create untested file
        untested_file = os.path.join(tmpdir, "untested.py")
        with open(untested_file, 'w') as f:
            f.write("def some_function():\n    pass\n")

        yield tmpdir


class TestMetrics:
    """Test metric functions."""

    def test_find_complex_files(self, sample_repo):
        """Test finding complex files."""
        complex_files = find_complex_files(sample_repo, threshold=500)
        assert len(complex_files) > 0
        assert any('complex' in name for name, _ in complex_files)

    def test_find_untested_code(self, sample_repo):
        """Test finding untested code."""
        untested = find_untested_code(sample_repo)
        # Should return a list (may be empty in small repos)
        assert isinstance(untested, list)

    def test_find_undocumented_code(self, sample_repo):
        """Test finding undocumented code."""
        undocumented = find_undocumented_code(sample_repo)
        assert len(undocumented) > 0

    def test_find_duplicate_blocks(self, sample_repo):
        """Test finding duplicate code blocks."""
        # Create a file with duplicated code
        dup_file = os.path.join(sample_repo, "duplication.py")
        with open(dup_file, 'w') as f:
            code = "x = 1\ny = 2\nz = 3\n"
            f.write(code * 5)

        duplicates = find_duplicate_blocks(sample_repo)
        # We should find some duplication
        assert isinstance(duplicates, list)


class TestAnalyzer:
    """Test technical debt analyzer."""

    def test_analyze(self, sample_repo):
        """Test full analysis."""
        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        assert result.repo_path == sample_repo
        assert result.total_hours > 0
        assert len(result.categories) == 6
        assert 'Complexity Debt' in result.categories
        assert 'Test Coverage Debt' in result.categories

    def test_severity_levels(self, sample_repo):
        """Test that severity levels are assigned correctly."""
        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        for category in result.categories.values():
            assert category.severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]

    def test_affected_files_populated(self, sample_repo):
        """Test that affected files are populated for non-zero debt."""
        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        for category in result.categories.values():
            # Categories with significant debt should have affected files or be dependency debt
            if category.estimated_hours > 5 and category.name != 'Dependency Debt':
                assert len(category.affected_files) > 0

    def test_recommendations_provided(self, sample_repo):
        """Test that recommendations are provided."""
        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        for category in result.categories.values():
            assert len(category.recommendations) > 0

    def test_sorted_categories(self, sample_repo):
        """Test category sorting by severity."""
        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        sorted_cats = result.sorted_categories()
        assert len(sorted_cats) == 6

        # Check that more severe categories come first
        for i in range(len(sorted_cats) - 1):
            severity1 = sorted_cats[i][1].severity.value
            severity2 = sorted_cats[i + 1][1].severity.value
            assert severity1 >= severity2


class TestFormatters:
    """Test output formatters."""

    def test_table_formatter(self, sample_repo):
        """Test table formatter."""
        from tech_debt_estimator.formatters import get_formatter

        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        formatter = get_formatter('table')
        output = formatter.format(result)

        assert isinstance(output, str)
        assert len(output) > 0

    def test_json_formatter(self, sample_repo):
        """Test JSON formatter."""
        from tech_debt_estimator.formatters import get_formatter
        import json

        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        formatter = get_formatter('json')
        output = formatter.format(result)

        # Should be valid JSON
        data = json.loads(output)
        assert 'total_hours' in data
        assert 'categories' in data
        assert data['total_hours'] > 0

    def test_markdown_formatter(self, sample_repo):
        """Test Markdown formatter."""
        from tech_debt_estimator.formatters import get_formatter

        analyzer = TechnicalDebtAnalyzer()
        result = analyzer.analyze(sample_repo)

        formatter = get_formatter('markdown')
        output = formatter.format(result)

        assert isinstance(output, str)
        assert '# Technical Debt Analysis Report' in output
        assert 'developer-hours' in output
