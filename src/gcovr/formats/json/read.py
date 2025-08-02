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

import json
import logging
import os
from glob import glob
from typing import Any

from ...data_model.coverage import GCOVR_DATA_SOURCES

from ...data_model import version
from ...data_model.container import CoverageContainer
from ...data_model.merging import get_merge_mode_from_options
from ...options import Options

LOGGER = logging.getLogger("gcovr")


#
#  Get coverage from already existing gcovr JSON files
#
def read_report(options: Options) -> CoverageContainer:
    """Read trace files into internal data model."""

    covdata = CoverageContainer()
    if len(options.json_add_tracefile) != 0:
        datafiles = set()

        for trace_files_regex in options.json_add_tracefile:
            trace_files = glob(trace_files_regex, recursive=True)
            if not trace_files:
                raise RuntimeError(
                    "Bad --json-add-tracefile option.\n"
                    "\tThe specified file does not exist."
                )

            for trace_file in trace_files:
                datafiles.add(os.path.normpath(trace_file))

        def deep_add_data_source(item: Any, data_source: str) -> None:
            """Extend the set of tuples with the current source file."""
            if isinstance(item, dict):
                if GCOVR_DATA_SOURCES in item:
                    item[GCOVR_DATA_SOURCES] = set(
                        (data_source, *e) for e in item[GCOVR_DATA_SOURCES]
                    )
                else:
                    item[GCOVR_DATA_SOURCES] = set((data_source,))
                for value in item.values():
                    deep_add_data_source(value, data_source)
            elif isinstance(item, list):
                for entry in item:
                    deep_add_data_source(entry, data_source)

        merge_options = get_merge_mode_from_options(options)
        for data_source in datafiles:
            LOGGER.debug(f"Processing JSON file: {data_source}")

            with open(data_source, encoding="UTF-8") as json_file:
                gcovr_json_data = json.load(json_file)

            format_version = str(gcovr_json_data["gcovr/format_version"])
            if format_version != version.FORMAT_VERSION:
                raise AssertionError(
                    f"Wrong format version, got {format_version} expected {version.FORMAT_VERSION}."
                )

            deep_add_data_source(gcovr_json_data["files"], data_source)

            covdata.merge(
                CoverageContainer.deserialize(
                    gcovr_json_data["files"],
                    options,
                ),
                merge_options,
            )

    return covdata
