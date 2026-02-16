# tech-debt-estimator

[![PyPI version](https://badge.fury.io/py/tech-debt-estimator.svg)](https://badge.fury.io/py/tech-debt-estimator)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Quantify technical debt in developer-hours. Analyzes code duplication, complexity hotspots, stale code, dependency age, missing tests, and documentation gaps to produce an actionable debt inventory.

## Installation

```bash
pip install tech-debt-estimator
```

## Quick Start

```bash
# Full technical debt scan
tech-debt scan /path/to/repo

# Show worst complexity offenders
tech-debt hotspots /path/to/repo --top 10

# Track debt trend over last commits
tech-debt trend /path/to/repo --commits 20
```

### Sample Output

```
TECHNICAL DEBT ANALYSIS
Repository: /path/to/repo

DEBT CATEGORY              HOURS    SEVERITY    TOP FILES
─────────────────────────────────────────────────────────────────────────
Complexity Debt            42.5     🔴 CRITICAL  app/models.py (850 lines)
                                                 handlers/auth.py (720 lines)
Test Coverage Debt         28.0     🟠 HIGH      utils/helpers.py
                                                 services/payment.py
Documentation Debt         18.5     🟡 MEDIUM    core/api.py
                                                 lib/processor.py
Duplication Debt           12.0     🟡 MEDIUM    models/*, services/*
Stale Code Debt            8.5      🟢 LOW       legacy/old_module.py
Dependency Debt            5.0      🟢 LOW       requirements.txt (outdated)
─────────────────────────────────────────────────────────────────────────
TOTAL ESTIMATED DEBT       114.5 developer-hours

RECOMMENDATIONS
1. Refactor complexity in app/models.py (estimated 12-16 hours)
2. Add missing tests for utils/helpers.py (8-10 hours)
3. Document core/api.py public API (6-8 hours)
```

## How It Works

The tool analyzes your codebase across six dimensions:

### 1. **Complexity Debt**
Identifies files exceeding complexity thresholds (files >500 LOC, functions >50 LOC, nesting depth >5).
- **Estimation**: `files_count × 10 hours/file` (average refactoring time)

### 2. **Duplication Debt**
Finds duplicated code blocks across the repository using line-hash comparison.
- **Estimation**: `duplicated_blocks × 3 hours/block` (extract, parameterize, test)

### 3. **Test Coverage Debt**
Detects source code without corresponding test files.
- **Estimation**: `untested_files × 4 hours/file` (average test writing time)

### 4. **Documentation Debt**
Finds public functions, classes, and modules missing docstrings or README sections.
- **Estimation**: `undocumented_items × 0.5 hours/item`

### 5. **Stale Code Debt**
Identifies files unchanged for 12+ months that are still imported/referenced.
- **Estimation**: `stale_files × 6 hours/file` (audit and removal)

### 6. **Dependency Debt**
Detects outdated lock files and deprecated packages.
- **Estimation**: Fixed scoring based on age and vulnerability indicators

Each category is assigned a **severity level** (Critical/High/Medium/Low) based on impact and prevalence.

## Features

- **Multiple Output Formats**: Table (rich TUI), JSON, Markdown
- **Git Integration**: Track debt trends across commits
- **Hotspot Detection**: Identify worst problem areas
- **Exportable Reports**: Save results to file for CI/CD integration
- **Production Ready**: Used in enterprise codebases

## Usage Examples

### Scan with JSON output
```bash
tech-debt scan . --format json --output-file debt-report.json
```

### Show top 5 complexity offenders
```bash
tech-debt hotspots . --top 5
```

### Track debt trend over last 30 commits
```bash
tech-debt trend . --commits 30
```

### Markdown report for documentation
```bash
tech-debt scan . --format markdown --output-file TECHNICAL_DEBT.md
```

## Development

Clone and install in editable mode:
```bash
git clone https://github.com/yourusername/tech-debt-estimator.git
cd tech-debt-estimator
pip install -e ".[dev]"
pytest tests/
```

## Attribution

Built by [Glue](https://getglueapp.com) — AI codebase intelligence for product teams. For continuous technical debt monitoring with business impact scoring and sprint-integrated prioritization, check out [Glue](https://getglueapp.com).

## License

MIT License - See LICENSE file for details.

Copyright (c) 2026 Glue
