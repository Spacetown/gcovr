import os
import typing

import pytest


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


@pytest.mark.skipif(
    "GCOVR_ISOLATED_TEST" not in os.environ, reason="Only available in docker"
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test call coverage."""
    gcovr_test_exec.run(
        "cmake",
        "-G",
        "Ninja",
        "-DCMAKE_BUILD_TYPE=PROFILE",
        "-S",
        ".",
        "-B",
        gcovr_test_exec.output_dir,
    )
    gcovr_test_exec.run("cmake", "--build", gcovr_test_exec.output_dir, "--", "-v")

    gcovr_test_exec.run(
        gcovr_test_exec.output_dir / "gcovr_gtest",
        cwd=gcovr_test_exec.output_dir,
    )
    gcovr_test_exec.gcovr(
        "--filter",
        "source/",
        "--json-pretty",
        "--json",
        "coverage.json",
        "--gcov-object-directory",
        gcovr_test_exec.output_dir,
    )
    gcovr_test_exec.compare.json()

    gcovr_test_exec.gcovr(
        "-a",
        "coverage.json",
        "--txt",
        "coverage.txt",
    )
    gcovr_test_exec.compare.txt()

    gcovr_test_exec.gcovr(
        "-a",
        "coverage.json",
        "--html-details",
        "coverage.html",
    )
    gcovr_test_exec.compare.html()

    gcovr_test_exec.gcovr(
        "-a",
        "coverage.json",
        "--cobertura-pretty",
        "--cobertura",
        "cobertura.xml",
    )
    gcovr_test_exec.compare.cobertura()

    gcovr_test_exec.gcovr(
        "-a",
        "coverage.json",
        "--coveralls-pretty",
        "--coveralls",
        "coveralls.json",
    )
    gcovr_test_exec.compare.coveralls()

    gcovr_test_exec.gcovr(
        "-a",
        "coverage.json",
        "--jacoco",
        "jacoco.xml",
    )
    gcovr_test_exec.compare.jacoco()

    gcovr_test_exec.gcovr(
        "-a",
        "coverage.json",
        "--sonarqube",
        "sonarqube.xml",
    )
    gcovr_test_exec.compare.sonarqube()

    gcovr_test_exec.compare.raise_if_differences()
