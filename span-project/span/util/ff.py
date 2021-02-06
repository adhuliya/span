#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The Feature Flag (ff) module contains the flags
and values for various system wide features."""

import logging
LOG = logging.getLogger("span")

import io

################################################################################
## BLOCK START: GLOBAL_FEATURE_FLAGS_AND_VALUES
################################################################################

# Initialize local arrays to a Top value for greater precision.
SET_LOCAL_ARRAYS_TO_TOP: bool = True

# Max number of analyses to be in synergy at a time
MAX_ANALYSES: int = 16

################################################################################
## BLOCK END  : GLOBAL_FEATURE_FLAGS_AND_VALUES
################################################################################

filterNames = {
  "io", "LOG", "logging",
  "filterNames", "filterAwayTheName",
  "printModuleAttributes",
}

def filterAwayTheName(name: str) -> bool:
  filterIt = False
  if name in filterNames:
    filterIt = True
  elif name.startswith("__"):
    filterIt = True
  return filterIt


def printModuleAttributes() -> str:
  """Prints the attributes in this module."""
  sio = io.StringIO()
  sio.write("Global Feature Flag Values (span.util.ff):\n")
  for key, val in globals().items():
    if filterAwayTheName(key): continue
    sio.write(f"  {key}: {val}\n")
  return sio.getvalue()


