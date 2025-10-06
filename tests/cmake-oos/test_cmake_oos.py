import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def test_makefile(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test CMake out of source build with makefile."""
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    generator = "MSYS Makefiles" if gcovr_test_exec.is_windows() else "Unix Makefiles"
    gcovr_test_exec.run(
        "cmake",
        "-G",
        generator,
        "-DCMAKE_BUILD_TYPE=PROFILE",
        "..",
        cwd=build_dir,
    )
    gcovr_test_exec.run(
        "make",
        cwd=build_dir,
    )

    gcovr_test_exec.run(
        build_dir / "testcase",
        cwd=build_dir,
    )
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
        "--cobertura-pretty",
        "--cobertura",
        "cobertura.xml",
    )
    gcovr_test_exec.compare.cobertura()

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
        "--sonarqube",
        "sonarqube.xml",
    )
    gcovr_test_exec.compare.sonarqube()

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
        "--coveralls-pretty",
        "--coveralls",
        "coveralls.json",
    )
    gcovr_test_exec.compare.coveralls()

    gcovr_test_exec.compare.raise_if_differences()


def test_ninja(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test CMake out of source build with ninja."""
    build_dir = gcovr_test_exec.output_dir / "build"
    build_dir.mkdir()
    gcovr_test_exec.run(
        "cmake",
        "-G",
        "Ninja",
        "-DCMAKE_BUILD_TYPE=PROFILE",
        "-S",
        "..",
        "-B",
        ".",
        cwd=build_dir,
    )
    gcovr_test_exec.run("cmake", "--build", build_dir, "--", "-v")

    gcovr_test_exec.run(
        build_dir / "testcase",
        cwd=build_dir,
    )
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
        "--cobertura-pretty",
        "--cobertura",
        "cobertura.xml",
    )
    gcovr_test_exec.compare.cobertura()

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
        "--sonarqube",
        "sonarqube.xml",
    )
    gcovr_test_exec.compare.sonarqube()

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
        "--coveralls-pretty",
        "--coveralls",
        "coveralls.json",
    )
    gcovr_test_exec.compare.coveralls()

    gcovr_test_exec.compare.raise_if_differences()
