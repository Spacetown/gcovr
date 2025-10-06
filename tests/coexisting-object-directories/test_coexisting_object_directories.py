from pathlib import Path
import typing


if typing.TYPE_CHECKING:
    from ..conftest import GcovrTestExec


def outputs(gcovr_test_exec: "GcovrTestExec") -> typing.Iterable[tuple[str, Path]]:
    """Build the executables."""
    for postfix in ["a", "b", "c"]:
        yield (postfix, gcovr_test_exec.output_dir / f"build.{postfix}")


def build(gcovr_test_exec: "GcovrTestExec") -> None:
    """Build the executables."""
    for postfix, build_dir in outputs(gcovr_test_exec):
        build_dir.mkdir()
        gcovr_test_exec.run(
            "cmake",
            "-G",
            "Ninja",
            "-DCMAKE_BUILD_TYPE=PROFILE",
            "-S",
            ".",
            "-B",
            build_dir,
            "-D",
            f"ODD={'OFF' if postfix == 'b' else 'ON'}",
        )
        gcovr_test_exec.run("cmake", "--build", build_dir, "--", "-v")


def run(gcovr_test_exec: "GcovrTestExec") -> None:
    """Run the executables."""
    gcovr_test_exec.run_parallel(
        *[
            ["sh", "-c", f"cd {build_dir} && ./parallel_call"]
            for _, build_dir in outputs(gcovr_test_exec)
        ]
    )


def report(gcovr_test_exec: "GcovrTestExec") -> None:
    """Generate the reports."""
    for postfix, _ in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "-a",
            f"coverage.{postfix}.json",
            "--txt",
            f"coverage.{postfix}.txt",
        )
    gcovr_test_exec.compare.txt()

    for postfix, _ in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "-a",
            f"coverage.{postfix}.json",
            "--cobertura-pretty",
            "--cobertura",
            f"cobertura.{postfix}.xml",
        )
    gcovr_test_exec.compare.cobertura()

    for postfix, _ in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "-a",
            f"coverage.{postfix}.json",
            "--coveralls-pretty",
            "--coveralls",
            f"coveralls.{postfix}.json",
        )
    gcovr_test_exec.compare.coveralls()

    for postfix, _ in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "-a",
            f"coverage.{postfix}.json",
            "--sonarqube",
            f"sonarqube.{postfix}.xml",
        )
    gcovr_test_exec.compare.sonarqube()

    gcovr_test_exec.compare.raise_if_differences()


def test_from_build_dir(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    build(gcovr_test_exec)
    run(gcovr_test_exec)
    for postfix, build_dir in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_test_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            "--root",
            gcovr_test_exec.output_dir,
            build_dir,
            cwd=build_dir,
        )
    gcovr_test_exec.compare.json()

    report(gcovr_test_exec)


def test_from_build_dir_without_object_dir(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    build(gcovr_test_exec)
    run(gcovr_test_exec)

    for postfix, build_dir in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_test_exec.output_dir / f"coverage.{postfix}.json",
            "--root",
            gcovr_test_exec.output_dir,
            build_dir,
            cwd=build_dir,
        )
    gcovr_test_exec.compare.json()

    report(gcovr_test_exec)


def test_from_build_dir_without_search_dir(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    build(gcovr_test_exec)
    run(gcovr_test_exec)

    for postfix, build_dir in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_test_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            "--root",
            gcovr_test_exec.output_dir,
            cwd=build_dir,
            env={"GCOV_STRIP": "99", "GCOV_PREFIX": str(build_dir)},
        )
    gcovr_test_exec.compare.json()

    report(gcovr_test_exec)


def test_from_root_dir(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    build(gcovr_test_exec)
    run(gcovr_test_exec)
    for postfix, build_dir in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_test_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            build_dir,
        )
    gcovr_test_exec.compare.json()

    report(gcovr_test_exec)


def test_from_root_dir_without_object_dir(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    build(gcovr_test_exec)
    run(gcovr_test_exec)

    for postfix, build_dir in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_test_exec.output_dir / f"coverage.{postfix}.json",
            build_dir,
        )
    gcovr_test_exec.compare.json()

    report(gcovr_test_exec)


def test_from_root_dir_without_search_dir(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test adding a tracefile output."""
    build(gcovr_test_exec)
    run(gcovr_test_exec)

    for postfix, build_dir in outputs(gcovr_test_exec):
        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json",
            gcovr_test_exec.output_dir / f"coverage.{postfix}.json",
            "--object-directory",
            build_dir,
            env={"GCOV_STRIP": "99", "GCOV_PREFIX": str(build_dir)},
        )
    gcovr_test_exec.compare.json()

    report(gcovr_test_exec)
