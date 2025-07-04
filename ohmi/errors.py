#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 15 10:30:19 2025

Copyright (c) 2025, Tommy Löfstedt. All rights reserved.

@author:  Tommy Löfstedt
@email:   tommy.lofstedt@umu.se
@license: BSD 3-clause.
"""
import enum
import warnings
import collections

__all__ = [
           "NotFoundError",
           "InvalidDicomError",
           "Escalation",
           "escalate",
           ]


class NotFoundError(RuntimeError):
    """An exception for when something sought is missing."""

    pass


class InvalidDicomError(RuntimeError):
    """An exception when a Dicom file couldn't be read."""

    pass


class Escalation(enum.Enum):
    """Constants for what to do when there's a problem."""

    NOTHING = "NOTHING"
    WARNING = "WARNING"
    ERROR = "ERROR"


def escalate(escalation: Escalation,
             message: str,
             error_postfix: str = "",
             warn_postfix: str = "",
             error: Exception = RuntimeError,
             warning: Warning = UserWarning,
             nothing: collections.abc.Callable[[], None] = lambda: None,
             ):
    """Escalate by reacting to the different escalation levels."""
    if escalation == Escalation.ERROR:
        raise error(message + error_postfix)
    elif escalation == Escalation.WARNING:
        warnings.warn(message + warn_postfix, warning)
    elif escalation == Escalation.NOTHING:
        nothing()  # Do something on nothing.
    else:
        raise ValueError(
            f"Escalation level not recognised ({escalation}).")
