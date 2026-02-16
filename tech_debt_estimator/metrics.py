"""Code metrics collection functions."""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set
from collections import defaultdict


# Patterns for code detection
PYTHON_PATTERN = re.compile(r'\.py$')
JS_PATTERN = re.compile(r'\.(js|ts|jsx|tsx)$')
CODE_PATTERNS = [PYTHON_PATTERN, JS_PATTERN]


def is_code_file(filepath: str) -> bool:
    """Check if file is a code file."""
    return any(pattern.search(filepath) for pattern in CODE_PATTERNS)


def get_lines_of_code(filepath: str) -> int:
    """Count non-comment, non-blank lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        code_lines = 0
        in_multiline_comment = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Handle Python multiline strings
            if '"""' in stripped or "'''" in stripped:
                in_multiline_comment = not in_multiline_comment
                continue

            # Skip if in multiline comment
            if in_multiline_comment:
                continue

            # Skip comment-only lines
            if stripped.startswith('#') or stripped.startswith('//'):
                continue

            code_lines += 1

        return code_lines
    except Exception:
        return 0


def find_complex_files(repo_path: str, threshold: int = 500) -> List[Tuple[str, int]]:
    """Find files exceeding complexity threshold (LOC)."""
    complex_files = []

    for root, dirs, files in os.walk(repo_path):
        # Skip common non-code directories
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build'}]

        for file in files:
            if is_code_file(file):
                filepath = os.path.join(root, file)
                loc = get_lines_of_code(filepath)

                if loc > threshold:
                    rel_path = os.path.relpath(filepath, repo_path)
                    complex_files.append((rel_path, loc))

    return sorted(complex_files, key=lambda x: x[1], reverse=True)


def hash_line_block(lines: List[str], block_size: int = 5) -> str:
    """Create hash of a block of lines."""
    block_text = '\n'.join(line.strip() for line in lines if line.strip())
    return hashlib.md5(block_text.encode()).hexdigest()


def find_duplicate_blocks(repo_path: str, block_size: int = 5) -> List[Dict]:
    """Find duplicated code blocks using line hashing."""
    hashes: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv', '.venv', '__pycache__'}]

        for file in files:
            if is_code_file(file):
                filepath = os.path.join(root, file)

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for i in range(len(lines) - block_size + 1):
                        block = lines[i:i + block_size]
                        block_hash = hash_line_block(block)
                        rel_path = os.path.relpath(filepath, repo_path)
                        hashes[block_hash].append((rel_path, i + 1))
                except Exception:
                    pass

    duplicates = []
    for block_hash, occurrences in hashes.items():
        if len(occurrences) > 1:
            duplicates.append({
                'hash': block_hash,
                'count': len(occurrences),
                'locations': occurrences
            })

    return sorted(duplicates, key=lambda x: x['count'], reverse=True)[:20]


def find_stale_files(repo_path: str, months: int = 12) -> List[Tuple[str, str]]:
    """Find files not modified in N months."""
    stale_files = []
    cutoff_date = datetime.now() - timedelta(days=30 * months)

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv', '.venv', '__pycache__'}]

        for file in files:
            if is_code_file(file):
                filepath = os.path.join(root, file)

                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < cutoff_date:
                        rel_path = os.path.relpath(filepath, repo_path)
                        last_modified = mtime.strftime('%Y-%m-%d')
                        stale_files.append((rel_path, last_modified))
                except Exception:
                    pass

    return sorted(stale_files, key=lambda x: x[1])


def find_untested_code(repo_path: str) -> List[str]:
    """Find source files without corresponding test files."""
    untested = []
    source_files = set()
    test_files = set()

    # Collect all source files and test files
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv', '.venv', '__pycache__'}]

        for file in files:
            if is_code_file(file):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, repo_path)

                if 'test' in filepath.lower() or 'spec' in filepath.lower():
                    test_files.add(rel_path)
                else:
                    source_files.add(rel_path)

    # Check for corresponding tests
    for source_file in source_files:
        has_test = False

        # Look for direct test matches
        for test_file in test_files:
            if source_file.replace('.py', '') in test_file or source_file.replace('.js', '') in test_file:
                has_test = True
                break

        if not has_test:
            untested.append(source_file)

    return sorted(untested)


def find_undocumented_code(repo_path: str) -> Dict[str, List[str]]:
    """Find Python/JS functions and classes missing docstrings."""
    undocumented = defaultdict(list)

    # Python pattern: def/class without docstring
    python_def_pattern = re.compile(r'^(\s*)(def|class)\s+(\w+)\s*[\(:]')
    docstring_pattern = re.compile(r'^\s*["\']{"3}|^\s*["\']{\'{3}')

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv', '.venv', '__pycache__'}]

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, repo_path)

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines):
                        match = python_def_pattern.match(line)
                        if match:
                            # Check if next non-empty line is a docstring
                            has_docstring = False
                            for j in range(i + 1, min(i + 5, len(lines))):
                                next_line = lines[j].strip()
                                if not next_line:
                                    continue
                                if docstring_pattern.match(lines[j]):
                                    has_docstring = True
                                break

                            if not has_docstring:
                                item_name = match.group(3)
                                undocumented[rel_path].append(item_name)
                except Exception:
                    pass

    return dict(undocumented)


def analyze_dependency_age(repo_path: str) -> Dict[str, any]:
    """Check age of dependency lock files."""
    result = {
        'has_requirements': False,
        'has_lock_file': False,
        'lock_file_age_days': None,
        'deprecated_packages': []
    }

    # Check for requirements files
    for fname in ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile.lock', 'package-lock.json', 'yarn.lock']:
        fpath = os.path.join(repo_path, fname)
        if os.path.exists(fpath):
            result['has_lock_file'] = True if 'lock' in fname else False
            if 'requirements' in fname or 'pyproject' in fname or 'setup' in fname:
                result['has_requirements'] = True

            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                age_days = (datetime.now() - mtime).days
                if result['lock_file_age_days'] is None or age_days < result['lock_file_age_days']:
                    result['lock_file_age_days'] = age_days
            except Exception:
                pass

    return result
