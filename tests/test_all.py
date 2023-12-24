from oglob import files
import pytest
import os


@pytest.fixture
def temp_test_dir(tmp_path):
    # Create files and directories
    (tmp_path / "file1.py").touch()
    (tmp_path / "file2.txt").touch()
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file3.py").touch()
    (tmp_path / "dir1" / "file4.jpg").touch()
    (tmp_path / "dir1" / "dir2").mkdir()
    (tmp_path / "dir1" / "dir2" / "file5.c").touch()

    # Create symbolic link
    os.symlink(tmp_path / "dir1", tmp_path / "link_dir")

    return tmp_path


def test_find_python_files(temp_test_dir):
    python_files = list(files(temp_test_dir, files.name(lambda f: f.endswith(".py"))))
    assert len(python_files) == 1
    assert python_files[0].name == "file1.py"


def test_recursive_search(temp_test_dir):
    python_files = list(
        files(
            temp_test_dir,
            files.name(lambda f: f.endswith(".py")),
            recursive=True,
            follow_symlinks=False,
        )
    )
    assert len(python_files) == 2
    assert set(f.name for f in python_files) == {"file1.py", "file3.py"}

    python_files = list(
        files(
            temp_test_dir,
            files.name(lambda f: f.endswith(".py")),
            recursive=True,
            follow_symlinks=True,
        )
    )
    assert len(python_files) == 3


def test_include_directories(temp_test_dir):
    items = list(
        files(temp_test_dir, files.full(lambda p: "dir1" in p), include_dir=True)
    )
    assert any(f.is_dir() for f in items)  # At least one directory is included


def test_symbolic_links(temp_test_dir):
    python_files = list(
        files(
            temp_test_dir,
            files.name(lambda f: f.endswith(".c")),
            recursive=True,
            follow_symlinks=False,
        )
    )
    assert len(python_files) == 1
    assert python_files[0].name == "file5.c"

    python_files = list(
        files(
            temp_test_dir,
            files.name(lambda f: f.endswith(".c")),
            recursive=True,
            follow_symlinks=True,
        )
    )
    assert len(python_files) == 2
    assert set(f.name for f in python_files) == {"file5.c", "file5.c"}


def test_root_is_name(temp_test_dir):
    python_files = list(
        files(temp_test_dir / "file1.py", files.name(lambda f: f.endswith(".py")))
    )
    assert len(python_files) == 1
    assert python_files[0].name == "file1.py"


def test_non_existing_name(temp_test_dir):
    with pytest.raises(FileNotFoundError):
        list(
            files(
                temp_test_dir / "non_existing_file",
                files.name(lambda f: f.endswith(".py")),
                missing_ok=False,
            )
        )
