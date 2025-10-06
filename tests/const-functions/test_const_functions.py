import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("testcase")
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json", "coverage.json")
    gcovr_test_exec.compare.json()

    gcovr_test_exec.gcovr(
        "-a",
        "coverage.json",
        "--json-summary-pretty",
        "--json-summary",
        "summary_coverage.json",
    )
    gcovr_test_exec.compare.json_summary()

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
