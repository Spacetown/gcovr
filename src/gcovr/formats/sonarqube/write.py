# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
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

from lxml import etree

from ...data_model.merging import get_merge_mode_from_options  # nosec # We only write XML files

from ...data_model.container import CoverageContainer
from ...options import Options
from ...utils import write_xml_output


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """Produce an XML report in the SonarQube generic coverage format."""
    covdata = covdata.deep_copy()
    covdata.merge_lines(get_merge_mode_from_options(options))

    root_elem = etree.Element("coverage")
    root_elem.set("version", "1")

    for _, filecov in sorted(covdata.items()):
        filename = filecov.presentable_filename(options.root_filter)

        file_node = etree.Element("file")
        file_node.set("path", filename)

        for linecov in sorted(
            filecov.lines.values(), key=lambda linecov: linecov.lineno
        ):
            if linecov.is_reportable:
                line_node = etree.Element("lineToCover")
                line_node.set("lineNumber", str(linecov.lineno))
                line_node.set("covered", "true" if linecov.is_covered else "false")

                if linecov.branches:
                    stat = linecov.branch_coverage()
                    line_node.set("branchesToCover", str(stat.total))
                    line_node.set("coveredBranches", str(stat.covered))

                file_node.append(line_node)

        root_elem.append(file_node)

    write_xml_output(
        root_elem,
        pretty=False,
        filename=output_file,
        default_filename="sonarqube.xml",
    )
