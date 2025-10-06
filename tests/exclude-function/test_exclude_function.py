import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test excluding of functions."""
    lambda_expressions_available = gcovr_test_exec.is_in_gcc_help("c++20")
    additional_options = []
    if lambda_expressions_available:
        additional_options += ["-std=c++20", "-DUSE_LAMBDA"]
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
        *additional_options,
    )

    gcovr_test_exec.run("testcase")
    process = gcovr_test_exec.gcovr(
        "--exclude-function",
        "sort_excluded_both()::{lambda(int, int)#2}::operator()(int, int) const",
        "--exclude-function",
        "/bar.+/",
        "--json-pretty",
        "--json",
        "coverage.json",
    )
    coverage_json_content = (gcovr_test_exec.output_dir / "coverage.json").read_text(
        encoding="utf-8"
    )
    if '"pos"' in coverage_json_content:
        assert (
            "Function exclude marker found on line 9:8 but no function definition found"
            not in process.stderr
        )

        def assert_stderr(string) -> None:
            assert string not in process.stderr
    else:

        def assert_stderr(string) -> None:
            assert string in process.stderr

    assert_stderr(
        "Function exclude marker found on line 9:8 but not supported for this compiler"
    )
    assert_stderr(
        "Function exclude marker found on line 9:51 but not supported for this compiler"
    )

    if lambda_expressions_available:
        assert_stderr(
            "Function exclude marker found on line 44:29 but not supported for this compiler"
        )
        assert_stderr(
            "Function exclude marker found on line 50:19 but not supported for this compiler"
        )
        assert_stderr(
            "Function exclude marker found on line 57:29 but not supported for this compiler"
        )
        assert_stderr(
            "Function exclude marker found on line 66:34 but not supported for this compiler"
        )
        assert_stderr(
            "Function exclude marker found on line 73:29 but not supported for this compiler"
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
