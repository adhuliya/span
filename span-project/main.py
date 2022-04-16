#!/usr/bin/env python3.6

# MIT License
# Copyright (C) 2021

"""
Python 3.6 or above.

This is the driver (main) module that invokes the SPAN.
This module is supposed to be aliased as `span`.

    chmod +x /<path-to-span-project>/main.py;
    sudo ln -s /<path-to-span-project>/main.py /usr/bin/span;

Once aliased, invoke `span -h` to get help with the command line options.
"""
import span.sys.driver as driver  # IMPORTANT
import span.util.logger as logger
import logging
LOG: logging.Logger = logging.getLogger(__name__)

from span.util.util import LS
import span.util.util as util

import os

# mainentry - when this module is run
if __name__ == "__main__":
  util.setupEnv()

  parser = driver.getParser()

  try: # TODO: add auto completion if present
    # ref: https://stackoverflow.com/questions/14597466/custom-tab-completion-in-python-argparse
    import argcomplete  # type: ignore
    argcomplete.autocomplete(parser)
  except:
    pass

  args = parser.parse_args()  # parse command line

  if util.LL1: LOG.info("\n\nSPAN_SYSTEM: STARTED!\n\n")

  if util.VV1: print("SPAN is:", os.path.realpath(__file__))
  if util.VV1: print("RotatingLogFile: file://",
                     logger.ABS_LOG_FILE_NAME, "\n\n", sep="")

  timer = util.Timer("TotalTimeTaken")
  args.func(args)             # take action
  timer.stopAndLog(util.VV0, util.LL0)

  if util.LL1: LOG.info("\n\nSPAN_SYSTEM: FINISHED!\n\n")


