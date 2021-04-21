#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Project wide utility functions.

This module imports the names from common_util that
are needed by this project.
"""

import logging
_LOG = logging.getLogger("span")

import sys

import span.util.ff as ff

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

LL = LL0 = LL1 = LL2 = LL3 = LL4 = LL5 = False
def setupLL(count):
  """Call this function to enact global LL settings."""
  global LL, LL0, LL1, LL2, LL3, LL4, LL5
  LL  = count
  LL0 = LL >= 0
  LL1 = LL >= 1
  LL2 = LL >= 2
  LL3 = LL >= 3
  LL4 = LL >= 4 # shows logs in the Host
  LL5 = LL >= 5 # shows logs in the Analyses spec too

VV:int = 0  # Verbosity. One of 0,1,2,3 (set via command line)
VV0 = VV1 = VV2 = VV3 = VV4 = VV5 = False
def setupVV(count):
  """Call this function to enact global VV settings."""
  global VV, VV0, VV1, VV2, VV3, VV4, VV5
  VV = count
  VV0 = VV >= 0
  VV1 = VV >= 1
  VV2 = VV >= 2
  VV3 = VV >= 3 # shows widening logs too
  VV4 = VV >= 4 # prints Top values in dfv too
  VV5 = VV >= 5 # prints id() of dfv objects too

DD:int = 0  # Detail. One of 0,1,2,3 (set via command line)
DD0 = DD1 = DD2 = DD3 = DD4 = DD5 = False
def setupDD(count):
  """Call this function to enact global DD settings."""
  global DD, DD0, DD1, DD2, DD3, DD4, DD5
  DD = count
  DD0 = DD >= 0
  DD1 = DD >= 1 # prints Top values in dfv too
  DD2 = DD >= 2
  DD3 = DD >= 3 # shows full variable names
  DD4 = DD >= 4
  DD5 = DD >= 5 # prints id() of dfv objects too

CC:int = 0  # Constraint Checks. One of 0,1,2,3 (set via command line)
CC0 = CC1 = CC2 = CC3 = CC4 = CC5 = False
def setupCC(count):
  """Call this function to enact global CC settings."""
  global CC, CC0, CC1, CC2, CC3, CC4, CC5
  CC = count
  CC0 = CC >= 0
  CC1 = CC >= 1
  CC2 = CC >= 2
  CC3 = CC >= 3
  CC4 = CC >= 4
  CC5 = CC >= 5

# A system wide feature switches
# The switches are used to dynamically enable or disable specific features.
# Use as follows:
#   from span.util.util import LS, US, AS

# by default all switches are false
LS = US = AS = GD = False  # IMPORTANT

# logger switch (enables the logging system)
# its good to enable while developing
#LS: bool = True # just comment this line to make it False

# dfv update switch (enforces monotonic updates)
# its good to disable when deploying
# just comment this line to make it False
#US: bool = True  # type: ignore

# assertion switch (enables deeper/costly correctness checking, like monotonicity)
# its good to enable while developing
#AS: bool = True  # just comment this line to make it False

# generate dot graph switch
# generate the dot graph output of the run of Span
#GD: bool = True # just comment this line to make it False

################################################
# BOUND END  : SystemWideSwitches
################################################


def setupEnv():
  """Setup some necessary things for the project globally."""
  sys.setrecursionlimit(ff.RECURSION_LIMIT)


