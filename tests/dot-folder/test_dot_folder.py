import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    gcovr_test_exec.cxx_link(
        ".subdir/testcase",
        *[
            gcovr_test_exec.cxx_compile(source, target=source + ".o", options=["-DFOO"])
            for source in [
                ".subdir/A/file1.cpp",
                ".subdir/A/file2.cpp",
                ".subdir/A/file3.cpp",
                ".subdir/A/file4.cpp",
                ".subdir/A/C/file5.cpp",
                ".subdir/A/C/D/file6.cpp",
                ".subdir/B/main.cpp",
            ]
        ],
    )

    gcovr_test_exec.run(".subdir/testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json",
        "coverage.json",
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
