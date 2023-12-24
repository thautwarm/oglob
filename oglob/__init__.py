"""
This module provides advanced file pattern matching functionality, similar to `glob.glob`,
but with enhanced features. It supports complex pattern matching using logical operators,
allowing users to search for files and directories based on custom criteria.

The module also includes options to search recursively,
include directories in the results, and choose whether to follow symbolic links.

Usage Example:

    ```python
    from pathlib import Path
    from oglob import files

    # Example of using the files function to find Python files
    pattern = files.name(lambda f: f.endswith('.py'))
    pattern &= files.sec(lambda p: 'tests' in p)

    pyfiles_in_test_dir = files('.', pattern, recursive=True)
    for file in pyfiles_in_test_dir:
        print(file)
    ```

Functions:
    files: The main function used for finding files and directories based on a pattern.

Classes:
    PathPattern: An abstract base class for defining file path patterns.

    (For internal use only)
    Path, File, Full, Sec: Concrete implementations of PathPattern for various matching criteria.
"""

from __future__ import annotations
from dataclasses import dataclass
import typing
import pathlib
import abc

__all__ = [
    "files",
    # for downstream abstractions only
    "PathPattern",
]


class files:
    """Lazily finds and yields files matching a specified pattern within a directory.

    This function is similar to `glob.glob` but offers more complex pattern matching and potentially better performance. It supports advanced pattern composition using logical operators such as `|` (OR), `&` (AND), `~` (NOT), and `-` (AND NOT).

    #### Parameters:
    - `root`: The root directory from which the search begins. If a string is provided, it's converted to a `pathlib.Path`.
    - `pattern`: The pattern to match against file paths, supporting logical operators for complex compositions.
    - `recursive`: If `True`, the function searches recursively through subdirectories. Defaults to `False`.
    - `include_dir`: If `True`, the search results include directories as well as files. Defaults to `False`.
    - `missing_ok`: If `True`, the function returns an empty iterable if the root directory does not exist. Defaults to `True`.

    #### Returns:
    An iterable of `pathlib.Path` objects representing files (and optionally directories) that match the given pattern.

    #### Example Usage:
    ```python
    # Find all Python files in the current directory
    pyfiles = files('.', files.name(lambda f: f.endswith('.py')))
    ```
    """

    def __new__(
        cls,
        root: pathlib.Path | str,
        pattern: PathPattern,
        recursive: bool = False,
        include_dir: bool = False,
        missing_ok: bool = True,
        follow_symlinks=True,
    ) -> typing.Iterable[pathlib.Path]:
        if isinstance(root, str):
            root = pathlib.Path(root).expanduser()
        if not root.exists():
            if missing_ok:
                return iter(())
            raise FileNotFoundError(f"Directory not found: '{root}'")

        config = _Config(
            pattern=pattern,
            recursive=recursive,
            include_dir=include_dir,
            follow_symlinks=follow_symlinks,
            cache=_ComputeCache(root, None, None),
        )

        return _unsafe_files_impl(root, config)

    @staticmethod
    def path(predicate: typing.Callable[[pathlib.Path], bool]):
        """Creates a pattern based on a predicate that matches the whole `Path` object.

        The predicate should take a `pathlib.Path` object and return a boolean indicating whether the path matches the desired criteria.

        #### Parameters:
        - `predicate`: A function that takes a `pathlib.Path` object and returns a boolean.

        #### Returns:
        A `PathPattern` object that can be used in the `files` function.

        #### Example:
        ```python
        # Pattern for matching Python files
        python_files_pattern = files.path(lambda p: p.suffix == '.py')
        python_files = files('.', python_files_pattern)
        ```
        """
        return Path(predicate)

    @staticmethod
    def name(predicate: typing.Callable[[str], bool]):
        """Creates a pattern based on a predicate that matches the file name.

        The predicate should take a string representing the file name (without the path) and return a boolean indicating whether the file name matches the desired criteria.

        #### Parameters:
        - `predicate`: A function that takes a file name as a string and returns a boolean.

        #### Returns:
        A `PathPattern` object suitable for use in the `files` function.

        #### Example:
        ```python
        # Pattern for finding JPEG images
        jpeg_image_pattern = files.name(lambda f: f.endswith('.jpg') or f.endswith('.jpeg'))
        jpeg_files = files('.', jpeg_image_pattern)
        ```
        """
        return File(predicate)

    @staticmethod
    def full(predicate: typing.Callable[[str], bool]):
        """Creates a pattern based on a predicate that matches the full path as a string.

        This allows patterns to be formed based on the entire path, including both the directory structure and the file name.

        NOTE: Unix-style path separators are used regardless of the platform.

        #### Parameters:
        - `predicate`: A function that takes a full file path as a string and returns a boolean.

        #### Returns:
        A `PathPattern` object for use with the `files` function.

        #### Example:
        ```python
        # Pattern for matching files in a 'src' directory
        src_files_pattern = files.full(lambda p: 'src' in p)
        ```
        """
        return Full(predicate)

    @staticmethod
    def sec(predicate: typing.Callable[[tuple[str, ...]], bool], absolute: bool = True):
        """Creates a pattern based on a predicate that matches the sections (parts) of the path.

        This allows for forming patterns based on specific segments of the path, such as directory names.

        #### Parameters:
        - `predicate`: A function that takes the parts of the path as a tuple of strings and returns a boolean.
        - `absolute`: If `True`, the absolute path is used; otherwise, the relative path is used. Defaults to `True`.

        #### Returns:
        A `PathPattern` object for use in the `files` function.

        #### Example:
        ```python
        # Pattern for matching files within any 'src' directory
        src_files_pattern = files.sec(lambda parts: 'src' in parts)
        ```
        """
        return Sec(predicate, absolute=absolute)


@dataclass
class _Config:
    pattern: PathPattern
    recursive: bool
    include_dir: bool
    follow_symlinks: bool
    cache: _ComputeCache


def _unsafe_files_impl(cur: pathlib.Path, config: _Config):
    # the existence of cur is guaranteed
    if not config.follow_symlinks and cur.is_symlink():
        return

    if cur.is_dir():
        # root directory should be included
        # if `include_dir` is set
        if config.include_dir:
            config.cache.reset(cur)
            if config.pattern._run(config.cache):
                yield cur
        yield from _unsafe_dir_files(cur, config)
    else:
        # handle the case where cur is not a directory
        config.cache.reset(cur)
        if config.pattern._run(config.cache):
            yield cur


def _unsafe_dir_files(curdir: pathlib.Path, config: _Config):
    """This file has some duplicated code for performance reasons."""
    not_follow_symlinks = not config.follow_symlinks
    for each in curdir.iterdir():
        if not_follow_symlinks and each.is_symlink():
            # we don't follow symlinks
            continue

        if each.is_dir():
            if config.include_dir:
                config.cache.reset(each)
                if config.pattern._run(config.cache):
                    yield each
            if config.recursive:
                yield from _unsafe_dir_files(each, config)
        else:
            config.cache.reset(each)
            if config.pattern._run(config.cache):
                yield each


@dataclass
class _ComputeCache:
    """There are two points to use this cache:

    1. avoiding recomputations:
        The absolute path and full path used for predicates on a given path are computed at most once.

    2. avoiding reallocations:
        Only one cache object is maintained for one path query, so that
        we can avoid repeated memory allocation and deallocation.
    """

    base: pathlib.Path
    absolute: pathlib.Path | None
    fullpath: str | None

    def reset(self, p: pathlib.Path):
        self.base = p
        self.absolute = None
        self.fullpath = None


class PathPattern(abc.ABC):
    def __or__(self, other):
        _check_arg(other)
        return OrPath(self, other)

    def __and__(self, other):
        _check_arg(other)
        return AndPath(self, other)

    def __invert__(self):
        return NotPath(self)

    def __sub__(self, other):
        _check_arg(other)
        return self & ~other

    @abc.abstractmethod
    def _run(self, cache: _ComputeCache) -> bool:
        raise NotImplementedError


def _check_arg(pattern):
    assert isinstance(pattern, PathPattern), (
        "pattern must be a 'PathPattern' object constructed via "
        "'files.name', 'files.path', 'files.full' or 'files.sec'."
    )


@dataclass
class Path(PathPattern):
    pred: typing.Callable[[pathlib.Path], bool]

    def _run(self, cache: _ComputeCache) -> bool:
        return self.pred(cache.base)


@dataclass
class File(PathPattern):
    pred: typing.Callable[[str], bool]

    def _run(self, cache: _ComputeCache) -> bool:
        return self.pred(cache.base.name)


@dataclass
class Full(PathPattern):
    pred: typing.Callable[[str], bool]

    def _run(self, cache: _ComputeCache) -> bool:
        fullpath = cache.fullpath
        if fullpath is None:
            absolute = cache.absolute
            if absolute is None:
                absolute = cache.absolute = cache.base.absolute()
            fullpath = cache.fullpath = absolute.as_posix()
        return self.pred(fullpath)


@dataclass
class Sec(PathPattern):
    pred: typing.Callable[[tuple[str, ...]], bool]
    absolute: bool = True

    def _run(self, cache: _ComputeCache) -> bool:
        absolute = cache.absolute
        if self.absolute:
            if absolute is None:
                absolute = cache.absolute = cache.base.absolute()
            return self.pred(absolute.parts)
        else:
            return self.pred(cache.base.parts)


@dataclass
class OrPath:
    lhs: PathPattern
    rhs: PathPattern

    def _run(self, cache: _ComputeCache) -> bool:
        return self.lhs._run(cache) or self.rhs._run(cache)


@dataclass
class AndPath:
    lhs: PathPattern
    rhs: PathPattern

    def _run(self, cache: _ComputeCache) -> bool:
        return self.lhs._run(cache) and self.rhs._run(cache)


@dataclass
class NotPath:
    pred: PathPattern

    def _run(self, cache: _ComputeCache) -> bool:
        return not self.pred._run(cache)
