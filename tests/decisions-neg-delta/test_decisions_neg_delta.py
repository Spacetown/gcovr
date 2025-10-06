import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "-std=c++11",
        "-O0",
        "main.cpp",
    )

    gcovr_test_exec.run("testcase")
    gcovr_test_exec.gcovr(
        "--verbose",
        "--decisions",
        "--json-pretty",
        "--json",
        "coverage.json",
    )
    gcovr_test_exec.compare.json()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--add-tracefile",
        "coverage.json",
        "--txt-metric",
        "decision",
        "-o",
        "coverage.txt",
    )
    gcovr_test_exec.compare.txt()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--add-tracefile",
        "coverage.json",
        "--decision",
        "--html-details",
        "coverage.html",
    )
    gcovr_test_exec.compare.html()

    gcovr_test_exec.compare.raise_if_differences()
