from pathlib import Path
import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test call coverage."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.c"),
    )

    gcovr_test_exec.run("testcase")
    first_json = Path("first.json")
    gcovr_test_exec.gcovr("--calls", "--json", first_json)

    gcovr_test_exec.run("testcase")
    second_json = Path("second.json")
    gcovr_test_exec.gcovr("--calls", "--json", second_json)

    gcovr_test_exec.gcovr(
        "-a",
        first_json,
        "-a",
        second_json,
        "--json",
        "coverage.json",
    )
    gcovr_test_exec.compare.json()

    gcovr_test_exec.gcovr(
        "--calls",
        "-a",
        "coverage.json",
        "--html",
        "--html-details",
        "coverage.html",
    )
    gcovr_test_exec.compare.html()

    gcovr_test_exec.compare.raise_if_differences()
