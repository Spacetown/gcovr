from contextlib import contextmanager
from pathlib import Path
import typing

import pytest

from tests.conftest import (
    GCOVR_ISOLATED_TEST,
    IS_DARWIN_HOST,
    USE_GCC_JSON_INTERMEDIATE_FORMAT,
    GcovrTestExec,
)


CHMOD_IS_WORKING = (
    not GCOVR_ISOLATED_TEST or IS_DARWIN_HOST or USE_GCC_JSON_INTERMEDIATE_FORMAT
)


@contextmanager
def chmod(mode: int, *paths: Path) -> typing.Iterator[None]:
    """Change mode during execution."""
    modes = []
    try:
        for path in paths:
            modes.append(path.stat().st_mode)
            path.chmod(mode)
        yield
    finally:
        for index, mode in enumerate(modes):
            paths[index].chmod(mode)


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
def test_ignore_output_error(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test ignoring GCOV output errors."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_test_exec.is_darwin() else 0o555,
        gcovr_test_exec.output_dir / "src",
        gcovr_test_exec.output_dir / "build",
    ):
        gcovr_test_exec.gcovr(
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--root",
            "src",
            "build",
        )
    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
def test_no_working_dir_found(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test gcov-no_working_dir_found logic."""

    (gcovr_test_exec.output_dir / "build").mkdir()
    gcovr_test_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_test_exec.is_darwin() else 0o555,
        gcovr_test_exec.output_dir / "src",
        gcovr_test_exec.output_dir / "build",
    ):
        gcovr_args = [
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--root=src",
            "build",
        ]
        if not gcovr_test_exec.use_gcc_json_format():
            gcovr_args.insert(0, "--gcov-ignore-errors=no_working_dir_found")
        gcovr_test_exec.gcovr(*gcovr_args)
    gcovr_test_exec.compare_json()
