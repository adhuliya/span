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
   getSize, )

################################################
# BOUND START: SystemWideSwitches
################################################

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


