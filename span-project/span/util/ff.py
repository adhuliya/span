#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The Feature Flags (ff) module contains the flags
and values for various system wide features.

This module imports no other modules in Span.
"""

import logging
_LOG = logging.getLogger("span")

import io

################################################################################
## BLOCK START: GLOBAL_FEATURE_FLAGS_AND_VALUES
################################################################################

# Set recursion limit
RECURSION_LIMIT = 5000

# Initialize local arrays to a Top value for greater precision.
SET_LOCAL_ARRAYS_TO_TOP: bool = True

# Initialize local variables to a Top value for greater precision.
SET_LOCAL_VARS_TO_TOP: bool = True

# Max number of analyses to be in synergy at a time
MAX_ANALYSES: int = 16

# IPA (ValueContext) Recursion Limit
IPA_VC_RECURSION_LIMIT: int = 200

# IPA (ValueContext) Reuse prev value context mapped Host? (optimization)
IPA_VC_RE_USE_PREV_VALUE_CONTEXT_HOST: bool = True

# IPA (ValueContext) widen the value context? (for termination)
IPA_VC_WIDEN_VALUE_CONTEXT: bool = False

# IPA (ValueContext) widen the value context depth. (for termination)
# depth = the max allowed count of a function in the current call string.
IPA_VC_MAX_WIDENING_DEPTH: int = 1


################################################################################
## BLOCK END  : GLOBAL_FEATURE_FLAGS_AND_VALUES
################################################################################

_filterNames = {
  "io", "_LOG", "logging",
  "filterNames", "_filterAwayTheName",
  "printModuleAttributes",
}

def _filterAwayTheName(name: str) -> bool:
  filterIt = False
  if name in _filterNames:
    filterIt = True
  elif name.startswith("__"):
    filterIt = True
  return filterIt


def getModuleAttributesString() -> str:
  """Converts the attributes in this module into a readable string."""
  sio = io.StringIO()
  sio.write("Global Feature Flag Values (span.util.ff):\n")
  for key, val in globals().items():
    if _filterAwayTheName(key): continue
    sio.write(f"  {key}: {val}\n")
  return sio.getvalue()


