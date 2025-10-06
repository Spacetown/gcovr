import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
        "switch_test.cpp",
    )

    gcovr_test_exec.run("testcase")
    gcovr_test_exec.gcovr(
        "--keep",
        "--verbose",
        "--decisions",
        "--json-pretty",
        "--json",
        "coverage.json.gz",
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--add-tracefile",
        "coverage.json.gz",
        "--json-pretty",
        "--json",
        "coverage.json",
    )
    gcovr_test_exec.compare.json()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--add-tracefile",
        "coverage.json.gz",
        "--decision",
        "--json-summary-pretty",
        "--json-summary",
        "summary_coverage.json",
    )
    gcovr_test_exec.compare.json_summary()

    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--add-tracefile",
        "coverage.json.gz",
        "--txt-metric",
        "decision",
        "--txt-summary",
        "-o",
        "coverage.txt",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.txt").write_text(
        process.stdout, encoding="utf-8"
    )
    gcovr_test_exec.compare.txt()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--add-tracefile",
        "coverage.json.gz",
        "--decision",
        "--html-details",
        "coverage.html",
    )
    gcovr_test_exec.compare.html()

    gcovr_test_exec.compare.raise_if_differences()
