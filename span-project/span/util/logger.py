#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Adds logging to the project.

How to use?
  STEP 1: Only during application initialization,
    |  import span.util.logger as logger # this module
    |  import logging
    |  _log: logging.Logger = None
    |
    |  def initialize():
    |    global _log
    |    logger.initLogger(appName="span", logLevel=logger.LogLevels.DEBUG)
    |    _log = logging.getLogger("span")
    |
    |  if __name__ == "__main__":
    |    initialize()
  STEP 2: For each module in the application,
    |  import logging
    |  _log = logging.getLogger("span")

Logging levels available:
    |  CRITICAL    50 logging.critical()
    |  ERROR       40 logging.error()
    |  WARNING     30 logging.warning()
    |  INFO        20 logging.info()
    |  DEBUG       10 logging.debug()
    |  NOTSET      0
"""

# Edit these configuration variables:

# THE LOGGER SWITCH (LS): if set to false, all guarded (by LS) logging shuts down.
# Creating an explicit Logger Switch is runtime efficient
# It benefits with ~20% speedup wrt to default logging disable mechanism.
ON: bool = True
OFF: bool = False
LS: bool = ON
# LS:  bool = OFF

DEFAULT_APP_NAME: str = "python-app"
LOGS_DIR: str = ".itsoflife/mydata/local/logs/{APP_NAME}-logs"
LOG_FILE_NAME: str = "{APP_NAME}.log"

ABS_LOG_FILE_NAME: str = ""  # initialized at runtime

LOG_FORMAT_1: str = (">>> %(asctime)s : %(levelname)8s : %(filename)s\n"
                     "    Line %(lineno)4s : %(funcName)s()\n"
                     "%(message)s\n")

LOG_FORMAT_2: str = ("   [%(asctime)s : %(levelname)8s : %(name)s : %(filename)s"
                     "    Line %(lineno)4s : %(funcName)s()]\n"
                     "%(message)s")

MAX_FILE_SIZE: int = 1 << 24  # in bytes 1 << 24 = 16 MB
BACKUP_COUNT: int = 5  # 5 x 16MB = 80 MB logs + one extra current 16 MB logfile.

import os
import os.path as osp
import logging
from typing import Optional
from enum import Enum

from logging.handlers import RotatingFileHandler

LOG: Optional[logging.Logger] = None

_ROOT_LOGGER: Optional[logging.Logger] = None
_INITIALIZED: bool = False


class LogLevels(Enum):
  """Logging Levels.

  Notes:
    CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
    For example, setting logging level to INFO,
    will enable INFO and DEBUG only.
  """
  CRITICAL = logging.CRITICAL
  ERROR = logging.ERROR
  WARNING = logging.WARNING
  INFO = logging.INFO
  DEBUG = logging.DEBUG
  NOTSET = logging.NOTSET


def createDir(dirPath: str) -> Optional[str]:
  """Creates dir. Relative paths use user's home.

  Args:
    dirPath: an absolute or relative path

  Returns:
    str: absolute path of the directory or None.

  """
  if osp.isabs(dirPath):
    absPath = dirPath
  else:
    userHome = os.getenv("HOME", "").strip()
    if userHome:
      absPath = osp.join(userHome, dirPath)
    else:
      logging.error("Unable to create dir '{}'. Env variable 'HOME' empty /not "
                    "available.".format(dirPath))
      return None

  try:
    os.makedirs(absPath, exist_ok=True)
  except Exception as e:
    logging.error("Error creating directory {},\n{}".format(absPath, e))
    return None

  return absPath


def initLogger(fileName: str = None,
    appName: str = DEFAULT_APP_NAME,
    logLevel: LogLevels = LogLevels.INFO,  # default logging level
    logFormat: str = LOG_FORMAT_2,
    maxFileSize: int = 1 << 26,
    backupCount=BACKUP_COUNT
) -> bool:
  """Initializes the logging system.

  Args:
    fileName:
    appName: one word app name (without space/ special chars)
    logLevel:
    logFormat:
    maxFileSize: in bytes
    backupCount:

  Returns:
    bool: True if logging setup correctly.
  """
  global _INITIALIZED, _ROOT_LOGGER, LOG, ABS_LOG_FILE_NAME
  if _INITIALIZED: return True

  # create log file dir
  if fileName:
    dirPath = osp.dirname(fileName)
    absPath = createDir(dirPath)
  else:
    dirPath = LOGS_DIR.format(APP_NAME=appName)
    absPath = createDir(dirPath)
    fileName = LOG_FILE_NAME.format(APP_NAME=appName)

  if not absPath:
    logging.error("%s: Cannot create logging dir: %s", appName, dirPath)
    return False

  absFileName = osp.join(absPath, fileName)
  ABS_LOG_FILE_NAME = absFileName

  logging.info(
    "{APP_NAME}: logs enabled: setting up logging system.".format(APP_NAME=appName))

  # set up root logger
  _ROOT_LOGGER = logging.getLogger()
  _ROOT_LOGGER.setLevel(logLevel.value)

  handler = RotatingFileHandler(absFileName,
                                maxBytes=maxFileSize,
                                backupCount=backupCount)
  handler.setFormatter(logging.Formatter(logFormat))

  _ROOT_LOGGER.handlers = []  # remove all previous handlers
  _ROOT_LOGGER.addHandler(handler)

  _ROOT_LOGGER.info("%s: Initialized with format : %s",
                    appName,
                    repr(logFormat))

  _LOG = logging.getLogger("span")

  _INITIALIZED = True
  return True


def disable():
  """Disables all logging.

  Disables all logging except CRITICAL.
  """
  global _INITIALIZED, _ROOT_LOGGER
  if _INITIALIZED:
    _ROOT_LOGGER.setLevel(LogLevels.CRITICAL)
    LOG.info("logging level changed to %s", LogLevels.CRITICAL)
    return True
  return False


def enable(logLevel=LogLevels.INFO):
  """Enables log_level severity and above.

  Args:
    logLevel: severity level to enable from (and above).
  """
  global _INITIALIZED, _ROOT_LOGGER
  if _INITIALIZED:
    _ROOT_LOGGER.setLevel(logLevel)
    LOG.info("logging level changed to %s", logLevel)
    return True
  return False


def setLevel(log_level=LogLevels.INFO):
  """Set _root_logger's log level, if already initialized

  Returns:
    bool: True if log level changed, false otherwise.
  """
  global _ROOT_LOGGER
  if _ROOT_LOGGER:
    _ROOT_LOGGER.setLevel(log_level)
    LOG.info("logging level changed to %s", log_level)
    return True  # changed log level
  return False  # not set


if __name__ == "__main__":
  initLogger()
