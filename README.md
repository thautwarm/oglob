[![Python Test](https://github.com/thautwarm/oglob/actions/workflows/python-test.yml/badge.svg?branch=main)](https://github.com/thautwarm/oglob/actions/workflows/python-test.yml)
[![PyPI version](https://img.shields.io/pypi/v/oglob.svg)](https://pypi.python.org/pypi/oglob)
[![MIT License](https://img.shields.io/badge/license-MIT-Green.svg?style=flat)](https://github.com/thautwarm/oglob/blob/main/LICENSE)

# `oglob`

The `oglob` is a Python module designed to offer composable file searching capabilities beyond the traditional `glob.glob` functionality. It enables users to perform complex pattern-based searches for files and directories within a file system, offering a blend of flexibility, performance, and ease of use.

The Key feature is the composable file pattern matching: Utilizes logical operators such as AND, OR, NOT, and AND NOT (DIFF) to construct intricate search patterns, allowing for precise file and directory selection criteria.

## Getting Started

The module is easy to integrate and use within any Python project. It's compatible with standard Python workflows and can be used alongside other file manipulation libraries.

```python
from oglob import files
root = '.'
pattern = files.sec(lambda parts: 'tests' in parts)
pattern &= files.path(lambda p: p.suffix == '.py')
required_files = files(root, pattern, recursive=True)
# required_files: Iterable[Path]
```

## API Reference

- `files(root: str | Path, pattern: PathPattern, ...)`, see the docstrings for more details.
- `files.sec(predicate: 'tuple[str, ...] -> bool') -> PathPattern`
- `files.full(predicate: 'str -> bool') -> PathPattern`
- `files.path(predicate: 'Path -> bool') -> PathPattern`
- `files.name(predicate: 'str -> bool') -> PathPattern`

For `PathPattern` objects, logical operators are supported:

- `p1 & p2`: `p1` and `p2` must be satisfied.
- `p1 | p2`: `p1` or `p2` must be satisfied.
- `~p`: `p` must not be satisfied.
- `p1 - p2`: `p1` must be satisfied, but `p2` must not be satisfied.

## Contributing

Feature enhancement, bug fixes, and documentation improvements are welcome, community input is highly valued.

## LICENSE

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
