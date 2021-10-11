#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""The Feature Flags (ff) module contains the flags
and values for various system wide features.

This module imports no other modules in Span.

Note: Keep all the flags in the global scope of this module.
"""

import logging
_LOG = logging.getLogger(__name__)

import io

LARGE_INT_VAL = 0x7FFFFFFF
"""Used for min value computations etc."""

################################################################################
## BLOCK START: GLOBAL_FEATURE_FLAGS_AND_VALUES
################################################################################

SET_LOCAL_ARRAYS_TO_TOP: bool = True
"""Initialize local arrays to a Top value for greater precision."""

SET_LOCAL_VARS_TO_TOP: bool = True
"""Initialize local variables to a Top value for greater precision."""

MAX_ANALYSES: int = 16
"""Max number of analyses to be executed simultaneously at a time."""

IPA_VC_RECURSION_LIMIT: int = 200
"""IPA (ValueContext) Recursion Limit."""

IPA_VC_RE_USE_PREV_VALUE_CONTEXT_HOST: bool = True
"""IPA (ValueContext) Reuse prev value context mapped Host? (optimization)."""

IPA_VC_WIDEN_VALUE_CONTEXT: bool = False
"""IPA (ValueContext) widen the value context? (for termination)."""

IPA_VC_MAX_WIDENING_DEPTH: int = 1
"""IPA (ValueContext) widen the value context depth. (for termination)
depth = the max allowed count of a function in the current call string.
It works only when `IPA_VC_WIDEN_VALUE_CONTEXT` is True."""

IPA_VC_REMOVE_UNUSED_VC = True
"""Remove value contexts not needed by any call site."""

IPA_VC_SAVE_MEMORY = False
"""Saves memory by merging too many contexts of a function."""

RECURSION_LIMIT = max(IPA_VC_RECURSION_LIMIT, 20000)
"""Set global recursion limit."""

################################################################################
## BLOCK END  : GLOBAL_FEATURE_FLAGS_AND_VALUES
################################################################################

# Set of attribute names that are not feature flags.
_filterFlagNames = {
  "io", "_LOG", "logging",
  "filterNames", "_filterAwayTheName",
  "printModuleAttributes",
}

def _canFilterAwayFlagName(name: str) -> bool:
  """Returns true if the name can be filtered away."""
  filterIt = False
  if name in _filterFlagNames:
    filterIt = True
  elif name.startswith("__"):
    filterIt = True
  return filterIt


def getModuleFlagsString() -> str:
  """Converts the flag names and values in the module into a readable string.
  This function can be used to print the flags set in the project,
  for logging and debugging purposes.
  """
  sio = io.StringIO()
  sio.write("Global Feature Flag Values (span.util.ff):\n")
  for key, val in globals().items(): # assumption: all flags are in global scope
    if _canFilterAwayFlagName(key): continue # discard irrelevant flag names
    sio.write(f"  {key}: {val}\n")
  return sio.getvalue()


