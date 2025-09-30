# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.4+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

# cspell:ignore addoption
from contextlib import contextmanager
import difflib
import logging
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess  # nosec
from sys import stderr
from typing import Callable, Iterable, Iterator, List, Optional, Union
from unittest import mock
import zipfile

import pytest
from lxml import etree  # nosec # Data is trusted.
from yaxmldiff import compare_xml

from gcovr.__main__ import main as gcovr_main

LOGGER = logging.getLogger(__name__)

IS_LINUX = platform.system() == "Linux"
IS_DARWIN = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

CC = os.environ["CC"]
CXX = os.environ["CXX"]
GCOV = os.environ.get("GCOV", "gcov").split(" ")

CC_HELP_OUTPUT = subprocess.run(  # nosec
    [CC, "--help", "--verbose"], capture_output=True, text=True, check=True
).stdout
CC_VERSION_OUTPUT = subprocess.run(  # nosec
    [CC, "--version"], capture_output=True, text=True, check=True
).stdout

CFLAGS = [
    "-fPIC",
    "-fprofile-arcs",
    "-ftest-coverage",
]
if "condition-coverage" in CC_HELP_OUTPUT:
    CFLAGS.append("-fcondition-coverage")
CXXFLAGS = CFLAGS.copy()

BASE_DIRECTORY = os.path.split(os.path.abspath(__file__))[0]
GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"

ARCHIVE_DIFFERENCES_FILE = os.path.join(BASE_DIRECTORY, "diff.zip")

# cspell:ignore Linaro xctoolchain
# look for a line "gcc WHATEVER VERSION.WHATEVER" in output like:
#   gcc-5 (Ubuntu/Linaro 5.5.0-12ubuntu1) 5.5.0 20171010
#   Copyright (C) 2015 Free Software Foundation, Inc.
#   This is free software; see the source for copying conditions.  There is NO
#   warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
if matches := re.search(r"^gcc\b.* ([0-9]+)\..+$", CC_VERSION_OUTPUT, re.M):
    IS_GCC = True
    REFERENCE_DIR_VERSION_LIST = [
        f"gcc-{version}"
        for version in range(5, int(matches.group(1)) + 1)
        if version != 7
    ]
    USE_GCC_JSON_INTERMEDIATE_FORMAT = "JSON format version: 2" in CC_VERSION_OUTPUT
# look for a line "WHATEVER clang version VERSION.WHATEVER" in output like:
#    Apple clang version 13.1.6 (clang-1316.0.21.2.5)
#    Target: arm64-apple-darwin21.5.0
#    Thread model: posix
#    InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
elif matches := re.search(r"\bclang version ([0-9]+)\.", CC_VERSION_OUTPUT, re.M):
    IS_GCC = False
    REFERENCE_DIR_VERSION_LIST = [
        f"clang-{version}" for version in range(10, int(matches.group(1)) + 1)
    ]
    USE_GCC_JSON_INTERMEDIATE_FORMAT = False
else:
    raise AssertionError(f"Unable to get compiler version from:\n{CC_VERSION_OUTPUT}")

CC_REFERENCE = REFERENCE_DIR_VERSION_LIST[-1]
REFERENCE_DIR_OS_SUFFIX = "" if IS_LINUX else f"-{platform.system()}"
REFERENCE_DIRS = list[str]()
for ref in REFERENCE_DIR_VERSION_LIST:  # pragma: no cover
    REFERENCE_DIRS.append(ref)
    if REFERENCE_DIR_OS_SUFFIX:
        REFERENCE_DIRS.append(f"{REFERENCE_DIRS[-1]}{REFERENCE_DIR_OS_SUFFIX}")
REFERENCE_DIRS.reverse()

RE_DECIMAL = re.compile(r"(\d+\.\d+)")

RE_CRLF = re.compile(r"\r\n")

RE_TXT_WHITESPACE_AT_EOL = re.compile(r"[ ]+$", flags=re.MULTILINE)

RE_LCOV_PATH = re.compile(r"(SF:)(?:.:)?/.+?((?:tests|doc)/.+?)?$", flags=re.MULTILINE)

RE_COBERTURA_SOURCE_DIR = re.compile(r"(<source>)(?:.:)?/.+?((?:tests/.+?)?</source>)")

RE_COVERALLS_CLEAN_KEYS = re.compile(r'"(commit_sha|repo_token)": "[^"]*"')
RE_COVERALLS_GIT = re.compile(
    r'"git": \{(?:"[^"]*": (?:"[^"]*"|\{[^\}]*\}|\[[^\]]*\])(?:, )?)+\}, '
)
RE_COVERALLS_GIT_PRETTY = re.compile(
    r'\s+"git": \{\s+"head": \{(?:\s+"[^"]+":.+\n)+\s+\},\s+"branch": "branch",\s+"remotes": \[[^\]]+\]\s+\},'
)


def pytest_addoption(parser: pytest.Parser) -> None:  # pragma: no cover
    """Return the additional options for pytest."""
    parser.addoption(
        "--generate_reference", action="store_true", help="Generate the reference"
    )
    parser.addoption(
        "--update_reference", action="store_true", help="Update the reference"
    )
    parser.addoption(
        "--archive_differences", action="store_true", help="Archive the different files"
    )
    parser.addoption(
        "--skip_clean", action="store_true", help="Skip the clean after the test"
    )


@contextmanager
def chdir(directory: Path) -> Iterator[None]:
    """Context for doing something in a locked directory."""
    current_dir = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(current_dir)


@contextmanager
def create_output(test_id: Optional[str], skip_clean: bool) -> Iterator[Path]:
    """Context for doing something in a locked directory."""
    output_dir = Path.cwd() / "output"
    if test_id is not None:
        output_dir /= test_id
    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        yield output_dir
    finally:
        if not skip_clean and output_dir.is_dir():
            shutil.rmtree(output_dir)


class GcovrTestCompare:
    """Class for comparing files."""

    def __init__(
        self,
        *,
        output_dir: Path,
        test_id: Optional[str],
        generate_reference: bool,
        update_reference: bool,
        archive_differences: bool,
    ):
        """Init the object."""
        self.output_dir = output_dir
        self.reference_root = Path.cwd() / "reference"
        if test_id is not None:
            self.reference_root /= test_id
        self.generate_reference = generate_reference
        self.update_reference = update_reference
        self.archive_differences = archive_differences
        self.whole_diff_output = list[str]()

    @staticmethod
    def __translate_newlines_if_windows(contents: str) -> str:
        return (
            RE_CRLF.sub(r"\n", contents) if platform.system() == "Windows" else contents
        )

    @staticmethod
    def __scrub_txt(contents: str) -> str:
        return RE_TXT_WHITESPACE_AT_EOL.sub("", contents)

    @staticmethod
    def __scrub_lcov(contents: str) -> str:
        return RE_LCOV_PATH.sub(r"\1\2", contents)

    @staticmethod
    def __scrub_xml(contents: str) -> str:
        contents = RE_DECIMAL.sub(lambda m: str(round(float(m.group(1)), 5)), contents)
        return contents

    @staticmethod
    def __scrub_cobertura(contents: str) -> str:
        contents = GcovrTestCompare.__scrub_xml(contents)
        contents = RE_COBERTURA_SOURCE_DIR.sub(r"\1\2", contents)
        return contents

    @staticmethod
    def __scrub_coveralls(contents: str) -> str:
        contents = RE_COVERALLS_CLEAN_KEYS.sub('"\\1": ""', contents)
        contents = RE_COVERALLS_GIT_PRETTY.sub("", contents)
        contents = RE_COVERALLS_GIT.sub("", contents)
        return contents

    def __find_reference_files(
        self, output_pattern: list[str]
    ) -> Iterable[tuple[Path, Path]]:
        seen_files = set()
        for reference_dir in [
            self.reference_root / reference_dir for reference_dir in REFERENCE_DIRS
        ]:
            if reference_dir.exists():
                for pattern in output_pattern:
                    for reference_file in reference_dir.glob(pattern):
                        if (test_file := reference_file.name) not in seen_files:
                            seen_files.add(test_file)
                            yield self.output_dir / test_file, reference_file

        if not seen_files:
            raise RuntimeError("No reference files found.")

    def __update_reference_data(  # pragma: no cover
        self, reference_file: Path, content: str, encoding: str
    ) -> Path:
        reference_file = self.reference_root / REFERENCE_DIRS[0] / reference_file.name
        reference_file.parent.mkdir(parents=True, exist_ok=True)

        with open(reference_file, "w", newline="", encoding=encoding) as out:
            out.write(content)

        return reference_file

    def __archive_difference_data(  # pragma: no cover
        self, test_scrubbed: str, reference_file: Path, encoding: str
    ) -> None:
        reference_file_zip = Path(
            REFERENCE_DIRS[0],
            reference_file.name,
        ).as_posix()
        encoded_string = test_scrubbed.encode(encoding)
        with zipfile.ZipFile(ARCHIVE_DIFFERENCES_FILE, mode="a") as fh_zip:
            fh_zip.writestr(reference_file_zip, encoded_string)

    def __remove_duplicate_data(  # pragma: no cover
        self,
        encoding: str,
        coverage: str,
        test_file: Path,
        reference_file: Path,
    ) -> None:
        # Loop over the other coverage data
        for reference_dir in [
            self.reference_root / reference_dir for reference_dir in REFERENCE_DIRS
        ]:  # pragma: no cover
            other_reference_file = reference_dir / test_file.name
            # ... and unlink the current file if it's identical to the other one.
            if (
                other_reference_file != reference_file
                and other_reference_file.is_file()
            ):  # pragma: no cover
                # Only remove it if we have no suffix or the other file has the same.
                if not REFERENCE_DIR_OS_SUFFIX or other_reference_file.name.endswith(
                    REFERENCE_DIR_OS_SUFFIX
                ):
                    with other_reference_file.open(encoding=encoding, newline="") as f:
                        if coverage == f.read():
                            os.unlink(reference_file)
                break
            # Check if folder is empty
            if reference_dir.exists() and len(list(reference_dir.glob("*"))) == 0:
                os.rmdir(str(reference_dir))

    @staticmethod
    def assert_equals(
        reference_file: Path, reference: str, test_file: Path, test: str, encoding: str
    ) -> None:
        """Assert that the given files are equal."""
        _, extension = os.path.splitext(reference_file)
        if extension in [".html", ".xml"]:
            if extension == ".html":
                el_reference = etree.fromstringlist(  # nosec # We parse our reference files here
                    reference.encode().split(b"\n"), etree.HTMLParser(encoding=encoding)
                )
                el_test = etree.fromstringlist(  # nosec # We parse our test files here
                    test.encode().split(b"\n"), etree.HTMLParser(encoding=encoding)
                )
            else:
                el_reference = etree.fromstringlist(  # nosec # We parse our reference files here
                    reference.encode().split(b"\n")
                )
                el_test = etree.fromstringlist(  # nosec # We parse our test files here
                    test.encode().split(b"\n")
                )

            diff_out: Optional[str] = compare_xml(el_reference, el_test)
            if diff_out is None:
                return

            diff_out = (
                f"-- {reference_file}\n++ {test_file}\n{diff_out}"  # pragma: no cover
            )
        else:
            reference_list = reference.splitlines(keepends=True)
            reference_list.append("\n")
            test_list = test.splitlines(keepends=True)
            test_list.append("\n")
            diff_lines = list[str](
                difflib.unified_diff(
                    reference_list,
                    test_list,
                    fromfile=str(reference_file),
                    tofile=str(test_file),
                )
            )

            diff_is_empty = len(diff_lines) == 0
            if diff_is_empty:
                return
            diff_out = "".join(diff_lines)  # pragma: no cover

        raise AssertionError(diff_out)  # pragma: no cover

    def __compare_files(
        self,
        *,
        output_pattern: list[str],
        scrub: Optional[Callable[[str], str]] = None,
        translate_new_line: bool = True,
        encoding: str = "utf8",
    ) -> None:
        for pattern in output_pattern:
            for generated_file in self.output_dir.glob(pattern):
                if self.generate_reference:  # pragma: no cover
                    reference_file = (
                        self.reference_root / REFERENCE_DIRS[0] / generated_file.name
                    )
                    if not reference_file.exists():
                        reference_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(generated_file, reference_file)

        for test_file, reference_file in self.__find_reference_files(output_pattern):
            with test_file.open(encoding=encoding, newline="") as fh_in:
                test_content = fh_in.read()
                if scrub is not None:
                    test_content = scrub(test_content)

            # Overwrite the file created above with the scrubbed content
            if self.generate_reference:  # pragma: no cover
                with reference_file.open("w", encoding=encoding, newline="") as fh_out:
                    fh_out.write(test_content)
                reference_content = test_content
            else:
                with reference_file.open(encoding=encoding, newline="") as fh_in:
                    reference_content = fh_in.read()

            try:
                self.assert_equals(
                    reference_file,
                    reference_content
                    if translate_new_line
                    else self.__translate_newlines_if_windows(reference_content),
                    test_file,
                    test_content
                    if translate_new_line
                    else self.__translate_newlines_if_windows(test_content),
                    encoding,
                )
            except AssertionError as e:  # pragma: no cover
                self.whole_diff_output.append(str(e) + "\n")
                if self.update_reference:
                    reference_file = self.__update_reference_data(
                        reference_file, test_content, encoding
                    )
                if self.archive_differences:
                    self.__archive_difference_data(
                        test_content, reference_file, encoding
                    )

            if self.generate_reference or self.update_reference:  # pragma: no cover
                self.__remove_duplicate_data(
                    encoding, test_content, test_file, reference_file
                )

    def raise_if_differences(self, prefix: Optional[str] = None) -> None:
        """Must be called at the end of the test to get the diff output."""
        diff_is_empty = len(self.whole_diff_output) == 0
        if prefix is None:
            prefix = ""
        message = f"{prefix}Diff output:\n{''.join(self.whole_diff_output)}Reference directories: {', '.join(REFERENCE_DIRS)}"
        self.whole_diff_output.clear()
        if not diff_is_empty:
            raise AssertionError(message)

    def json(self) -> None:
        """Compare the JSON output files."""
        self.__compare_files(
            output_pattern=["coverage*.json"],
        )

    def json_summary(self) -> None:
        """Compare the JSON summary output files."""
        self.__compare_files(
            output_pattern=["summary_coverage*.json"],
        )

    def txt(self) -> None:
        """Compare the text output files."""
        self.__compare_files(
            output_pattern=["coverage*.txt"],
            scrub=self.__scrub_txt,
        )

    def markdown(self) -> None:
        """Compare the markdown output files."""
        self.__compare_files(
            output_pattern=["coverage*.md"],
            scrub=self.__scrub_txt,
        )

    def html(self, encoding: str = "utf8") -> None:
        """Compare the HTML report files."""
        self.__compare_files(
            output_pattern=["coverage*.html", "coverage*.css"],
            scrub=self.__scrub_txt,
            encoding=encoding,
        )

    def csv(self) -> None:
        """Compare the CSV output files."""
        self.__compare_files(
            output_pattern=["coverage*.csv"],
            scrub=self.__scrub_txt,
            translate_new_line=False,
        )

    def clover(self) -> None:
        """Compare the clover output files."""
        self.__compare_files(
            output_pattern=["clover*.xml"],
            scrub=self.__scrub_xml,
        )

    def cobertura(self) -> None:
        """Compare the cobertura output files."""
        self.__compare_files(
            output_pattern=["cobertura*.xml"],
            scrub=self.__scrub_cobertura,
        )

    def coveralls(self) -> None:
        """Compare the coveralls output files."""
        self.__compare_files(
            output_pattern=["coveralls*.json"],
            scrub=self.__scrub_coveralls,
        )

    def jacoco(self) -> None:
        """Compare the jacoco output files."""
        self.__compare_files(
            output_pattern=["jacoco*.xml"],
            scrub=self.__scrub_xml,
        )

    def lcov(self) -> None:
        """Compare the LCOV output files."""
        self.__compare_files(
            output_pattern=["coverage*.lcov"],
            scrub=self.__scrub_lcov,
        )

    def sonarqube(self) -> None:
        """Compare the sonarqube output files."""
        self.__compare_files(
            output_pattern=["sonarqube*.xml"],
        )


class GcovrTestExec:
    """Builder to compile the test executable."""

    def __init__(
        self,
        *,
        output_dir: Path,
        compare: GcovrTestCompare,
    ):
        """Init the builder."""
        self.compare = compare
        self.output_dir = output_dir

    @staticmethod
    def is_linux() -> bool:
        """Query if we are running under Linux."""
        return IS_LINUX

    @staticmethod
    def is_darwin() -> bool:
        """Query if we are running under MacOs."""
        return IS_DARWIN

    @staticmethod
    def is_windows() -> bool:
        """Query if we are running under Windows."""
        return IS_WINDOWS

    @staticmethod
    def is_gcc() -> bool:
        """Query if we are testing with GCC."""
        return IS_GCC

    @staticmethod
    def is_llvm() -> bool:
        """Query if we are testing with LLVM/clang."""
        return not IS_GCC

    @staticmethod
    def use_gcc_json_format() -> bool:
        """Query if we can use the GCC JSON intermediate format."""
        return USE_GCC_JSON_INTERMEDIATE_FORMAT

    @staticmethod
    def gcov() -> list[str]:
        """Get the gcov command to use."""
        return GCOV

    def copy_source(self, source_from: Optional[str] = None) -> None:
        """Copy the test data to the output."""
        if source_from is None:
            data = Path.cwd() / "source"
        else:
            data = Path.cwd().parent / source_from / "source"
        for entry in data.glob("*"):
            if entry.is_dir():
                shutil.copytree(entry, self.output_dir / entry.name)
            else:
                shutil.copy(entry, self.output_dir)

    def run(
        self,
        *args: Union[str, Path],
        env: Optional[dict[str, str]] = None,
        cwd: Optional[Path] = None,
    ) -> None:
        """Run the given arguments."""
        cmd = [*args]
        if cwd is None:
            cwd = self.output_dir
        executable = Path(cmd[0])
        if not executable.is_absolute():
            if (cwd / executable).exists():
                executable = cwd / executable
            else:
                executable = shutil.which(executable)
                if executable is None:
                    raise RuntimeError(f"Can't resolve path {args[0]}.")
            cmd[0] = executable
        cmd = [str(arg) for arg in cmd]
        print(
            f"\nRunning in {cwd.relative_to(Path.cwd())}: {' '.join(cmd)}", file=stderr
        )
        new_env = os.environ.copy()
        if env:
            new_env.update(env)

        subprocess.run(  # nosec
            cmd,
            check=True,
            env=new_env,
            cwd=str(cwd),
        )
        print("-------------- done --------------\n", file=stderr)

    def run_parallel(
        self,
        *args_list: list[str],
        env: Optional[dict[str, str]] = None,
        cwd: Optional[Path] = None,
    ) -> None:
        """Run the given arguments."""
        processes = list[subprocess.Popen]()
        for index, args in enumerate(args_list, start=1):
            if cwd is None:
                cwd = self.output_dir
            executable = Path(args[0])
            if not executable.is_absolute():
                if (cwd / executable).exists():
                    executable = cwd / executable
                else:
                    executable = shutil.which(executable)
                    if executable is None:
                        raise RuntimeError(f"Can't resolve path {args[0]}.")
                args = [executable, *args[1:]]
            args = [str(arg) for arg in args]
            print(
                f"\n[{index}] Starting in {cwd.relative_to(Path.cwd())}: {' '.join(args)}",
                file=stderr,
            )
            new_env = os.environ.copy()
            if env:
                new_env.update(env)

            processes.append(
                subprocess.Popen(  # nosec
                    args,
                    env=new_env,
                    cwd=str(cwd),
                )
            )

        for index, process in enumerate(processes, start=1):
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, f"Process [{index}]"
                )

            print(f"\n[{index}] done", file=stderr)

    def cc(self, *args: Union[str, Path]) -> None:
        """Run CC with the given arguments."""
        self.run(CC, *CFLAGS, *args)

    def cxx(self, *args: Union[str, Path]) -> None:
        """Run CXX with the given arguments."""
        self.run(CXX, *CXXFLAGS, *args)

    def cc_compile(
        self,
        source: Union[str, Path],
        *,
        target: Optional[str] = None,
        options: Optional[List[str]] = None,
    ) -> Path:
        """Compile the given source and return the target."""
        target_absolute = self.output_dir / (
            (Path(source).name + ".o") if target is None else target
        )
        if options is None:
            options = []
        self.cc(*options, "-c", source, "-o", target_absolute)
        return target_absolute

    def cxx_compile(
        self,
        source: Union[str, Path],
        *,
        target: Optional[str] = None,
        options: Optional[List[str]] = None,
    ) -> Path:
        """Compile the given source and return the target."""
        target_absolute = self.output_dir / (
            (Path(source).name + ".o") if target is None else target
        )
        if options is None:
            options = []
        self.cxx(*options, "-c", source, "-o", target_absolute)
        return target_absolute

    def cc_link(self, executable: Union[str, Path], *objects: Union[str, Path]) -> Path:
        """Link the given objects and return the full path of the executable."""
        target = self.output_dir / executable
        self.cc(*objects, "-o", target)
        return target

    def cxx_link(self, executable: str, *objects: Union[str, Path]) -> Path:
        """Link the given objects and return the full path of the executable."""
        target = self.output_dir / executable
        self.cxx(*objects, "-o", target)
        return target

    def gcovr(
        self,
        *args: Union[str, Path],
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
        use_main: bool = False,
    ) -> None:
        """Run GCOVR with the given arguments"""
        if env is None:
            env = dict[str, str]()
        if use_main:
            with chdir(cwd or self.output_dir):
                with mock.patch.dict(os.environ, env):
                    gcovr_main([str(a) for a in args])
        else:
            self.run("gcovr", *args, cwd=cwd, env=env)


@pytest.fixture(scope="function")
def gcovr_test_exec(request: pytest.FixtureRequest) -> Iterable[GcovrTestExec]:
    """Test fixture to build an object/executable and run gcovr tool with comparison of files."""
    skip_clean = True  # request.config.getoption("skip_clean")
    function_name = request.node.name
    parameter = None
    if "[" in function_name:
        function_name, parameter = function_name.split("[", maxsplit=1)
        parameter = parameter[:-1]
    test_id_parts = list[str]()
    if function_name != "test":
        test_id_parts.append(function_name[5:])
    if parameter is not None:
        test_id_parts.append(parameter)
    test_id = "-".join(test_id_parts)
    with chdir(request.path.parent) as output_dir:
        with create_output(test_id, skip_clean) as output_dir:
            test_exec = GcovrTestExec(
                output_dir=output_dir,
                compare=GcovrTestCompare(
                    output_dir=output_dir,
                    test_id=test_id,
                    generate_reference=request.config.getoption("generate_reference"),
                    update_reference=request.config.getoption("update_reference"),
                    archive_differences=request.config.getoption("archive_differences"),
                ),
            )
            if Path("source").is_dir():
                test_exec.copy_source()
            elif "SOURCE_FROM" in request.module.__dict__:
                test_exec.copy_source(request.module.__dict__["SOURCE_FROM"])

            yield test_exec
            test_exec.compare.raise_if_differences(
                "Call to gcovr_test_exec.compare.raise_if_differences() missing at end of test.\n"
            )
