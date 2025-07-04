#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 14:03:57 2025

Copyright (c) 2025, Tommy Löfstedt. All rights reserved.

@author:  Tommy Löfstedt
@email:   tommy.lofstedt@umu.se
@license: BSD 3-clause.
"""
import typing
import pathlib
import dataclasses

import numpy as np
import numpy.typing

import utils

__all__ = ["settings",
           "find_files",
           "verbose"]


@dataclasses.dataclass
class Settings(object):
    """A class to keep track of settings."""

    dtype: np.typing.DTypeLike = np.float32
    verbosity: int = 1

    # def __init__(self,
    #              dtype: np.typing.DTypeLike = np.float32,
    #              ):
    #     self.dtype = dtype


settings = Settings()


def find_files(path: pathlib.Path,
               patterns: typing.Union[str, list[str], tuple[str], None] = None,
               verbosity: int = 0,
               ) -> list[pathlib.Path]:
    """Find the files matching the pattern from the given directory."""
    if patterns is None:
        patterns = ["*"]
    elif isinstance(patterns, str):
        patterns = [patterns]

    # Find the files
    files = []
    utils.verbose("utils.find_files",
                  f"Reading directory '{path}'.",
                  1, verbosity)
    for pattern in patterns:
        utils.verbose("utils.find_files",
                      f"Filtering by pattern: '{pattern}'.",
                      2, verbosity)
        for fname in path.glob(pattern):
            utils.verbose("utils.find_files",
                          f"Found file: '{fname}'",
                          3, verbosity)
            files.append(fname)

    return files


def verbose(who: str,
            text: str,
            level: int = 2,
            verbosity: int = 0,
            ):
    """Print given text if the verbosity is at or above the given level."""
    if verbosity >= level:
        print(f"[{who}]: {text}")
