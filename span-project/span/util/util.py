#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Project wide utility functions."""

import logging

LOG = logging.getLogger("span")

# Import just the entities that are being used in the current project:
from span.util.common_util import \
  (createDir,
   readFromFile,
   writeToFile,
   appendToFile,
   getUniqueId,
   exitIfProgramDoesnotExist,
   getSize2,
   Timer,
   programExists,
   )

################################################
# BOUND START: SystemWideSwitches
################################################

VV:int = 0  # Verbosity. One of 0,1,2,3 (set via command line)
VV0 = VV1 = VV2 = VV3 = False
def setupVV():
  """Call this function after setting VV value."""
  global VV, VV0, VV1, VV2, VV3
  VV0 = VV >= 0
  VV1 = VV >= 1
  VV2 = VV >= 2
  VV3 = VV >= 3

CC:int = 0  # Constraint Checks. One of 0,1,2,3 (set via command line)
CC0 = CC1 = CC2 = CC3 = False
def setupCC():
  """Call this function after setting CC value."""
  global CC, CC0, CC1, CC2, CC3
  CC0 = CC >= 0
  CC1 = CC >= 1
  CC2 = CC >= 2
  CC3 = CC >= 3

# A system wide feature switches
# The switches are used to dynamically enable or disable specific features.
# Use as follows:
#   from span.util.util import LS, US, AS

# by default all switches are false
LS = US = AS = GD = False  # IMPORTANT

# logger switch (enables the logging system)
# its good to enable while developing
LS: bool = True # just comment this line to make it False

# dfv update switch (enforces monotonic updates)
# its good to disable when deploying
# just comment this line to make it False
US: bool = True  # type: ignore

# assertion switch (enables deeper/costly correctness checking, like monotonicity)
# its good to enable while developing
#AS: bool = True  # just comment this line to make it False

# generate dot graph switch
# generate the dot graph output of the run of Span
# GD: bool = True # just comment this line to make it False

################################################
# BOUND END  : SystemWideSwitches
################################################


