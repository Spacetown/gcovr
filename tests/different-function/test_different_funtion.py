from pathlib import Path
import subprocess
import typing

import pytest


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def outputs(gcovr_test_exec: "GcovrTestExec") -> typing.Iterable[tuple[int, Path]]:
    """Build the executables."""
    for postfix in [1, 2]:
        yield (postfix, gcovr_test_exec.output_dir / f"build{postfix}")


@pytest.mark.parametrize(
    "merge_mode_function",
    [
        "strict",
        "merge-use-line-0",
        "merge-use-line-min",
        "merge-use-line-max",
        "separate",
    ],
)
def test(gcovr_test_exec: "GcovrTestExec", merge_mode_function) -> None:
    """Test adding a tracefile output."""
    for postfix, build_dir in outputs(gcovr_test_exec):
        build_dir.mkdir()
        additional_options = []
        if postfix == 2:
            additional_options.append("-DFOO_OTHER_LINE")
        gcovr_test_exec.cxx_link(
            "testcase",
            *additional_options,
            "../main.c",
            cwd=build_dir,
        )

    gcovr_test_exec.run_parallel(
        *[
            ["sh", "-c", f"cd {build_dir} && ./testcase"]
            for _, build_dir in outputs(gcovr_test_exec)
        ]
    )

    if merge_mode_function == "strict":
        # Test exitcode for strict mode
        with pytest.raises(subprocess.CalledProcessError) as exception:
            gcovr_test_exec.gcovr(
                "--json-pretty",
                "--json",
                "coverage.json",
            )
        assert exception.value.returncode == 64, "Read error."
    else:
        additional_options = [f"--merge-mode-functions={merge_mode_function}"]
        gcovr_test_exec.gcovr(
            "--verbose",
            *additional_options,
            "--json-pretty",
            "--json",
            "coverage.json",
        )
        gcovr_test_exec.compare.json()

        if merge_mode_function == "separate":
            # Test exitcode for merging JSON with strict mode
            with pytest.raises(subprocess.CalledProcessError) as exception:
                gcovr_test_exec.gcovr(
                    "-a",
                    "coverage.json",
                    "--json-pretty",
                    "--json",
                    "coverage.error.json",
                )
            assert exception.value.returncode == 64, "Read error."
        else:
            additional_options.clear()

        gcovr_test_exec.gcovr(
            "-a",
            "coverage.json",
            *additional_options,
            "--txt",
            "coverage.txt",
        )
        gcovr_test_exec.compare.txt()

        gcovr_test_exec.gcovr(
            "-a",
            "coverage.json",
            *additional_options,
            "--html-details",
            "coverage.html",
        )
        gcovr_test_exec.compare.html()

        gcovr_test_exec.gcovr(
            "-a",
            "coverage.json",
            *additional_options,
            "--cobertura-pretty",
            "--cobertura",
            "cobertura.xml",
        )
        gcovr_test_exec.compare.cobertura()

        gcovr_test_exec.gcovr(
            "-a",
            "coverage.json",
            *additional_options,
            "--coveralls-pretty",
            "--coveralls",
            "coveralls.json",
        )
        gcovr_test_exec.compare.coveralls()

        gcovr_test_exec.gcovr(
            "-a",
            "coverage.json",
            *additional_options,
            "--sonarqube",
            "sonarqube.xml",
        )
        gcovr_test_exec.compare.sonarqube()

    gcovr_test_exec.compare.raise_if_differences()
