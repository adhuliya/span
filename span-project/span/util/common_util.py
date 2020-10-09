#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Common utility functions module which can be used in any project.
Note(AD): This file is hard-linked to the `snippets` repo that
contains various common utility modules.
"""

import os
import os.path as osp
import sys
import subprocess as subp
import shutil
from typing import Optional as Opt, Set, Generator, List, Callable
import time

import logging

LOG = logging.getLogger("span")

LS = True  # never comment this line
"""Logging Switch: to disable set it to false."""

globalCounter: int = 0
RelFilePathT = str  # a relative file path (could be absolute too)
AbsFilePathT = str  # an absolute file path
TEXT_CHARS = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})

Verbosity = 0  # One of 0,1,2,3 (set via command line)

################################################
# BLOCK START: FileSystem_Related
################################################

def createDir(dirPath, existOk=True):
  """Creates dir. Relative paths use current directory.

  Args:
    dirPath: an absolute or relative path

  Returns:
    str: absolute path of the directory or None.
  """
  absPath = getAbolutePath(dirPath)
  if LS: LOG.debug("Creating directory %s", absPath)

  try:
    os.makedirs(absPath, exist_ok=existOk)
  except Exception as e:
    if LS: LOG.error("Error creating directory {},\n{}".format(absPath, e))
    return None

  return absPath


def removeFileIfExists(filePath: str) -> None:
  """Removes the file if it exists."""
  if osp.exists(filePath):
    if not osp.isdir(filePath):
      os.remove(filePath)
    else:
      if LS: LOG.error(f"The given file is a directory.: {filePath}")


def getAbolutePath(filePath: str):
  """Returns absolute version of the given file path."""
  return osp.abspath(filePath)


def readFromFile(fileName: str) -> str:
  """Returns the complete content of the given file."""
  with open(fileName) as f:
    return f.read()


def writeToFile(fileName: str, content: str):
  """Writes content to the given file."""
  with open(fileName, "w") as f:
    f.write(content)
  return None


def appendToFile(fileName: str, content: str):
  """Writes content to the given file."""
  with open(fileName, "a") as f:
    f.write(content)
  return None


def getAllFilePaths(directory: str) -> Generator[str, None, None]:
  """Returns the full file names of all the files
  (recursively) withing the given directory."""
  for root, dirs, files in os.walk(directory):
    for d in dirs:
      path = osp.join(root, d)
      yield path
    for f in files:
      path = osp.join(root, f)
      yield path


def isEmptyDir(directory: str) -> bool:
  lst = os.listdir(directory)
  return len(lst) == 0


def isBinaryFile(filePath: RelFilePathT) -> bool:
  """A rough check to know if the file has non-textual content."""
  isBinaryString = \
    lambda bytes: bool(bytes.translate(table=None, delete=TEXT_CHARS))
  return isBinaryString(open(filePath, "rb").read(1024))


def getScriptRelativeFilePath(relFileName: str) -> Opt[str]:
  """Takes a file name relative to this scripts location
  and returns an absolute path.
  """
  if osp.isabs(relFileName):
    print("ERROR: relative file name exptected:", relFileName)
    return None
  thisScriptPath = osp.realpath(__file__)
  thisScriptDir = osp.dirname(thisScriptPath)
  absFilePath = osp.join(thisScriptDir, relFileName)
  return absFilePath


def copyDirectoryContents(srcDir: RelFilePathT, destDir: RelFilePathT) -> None:
  """Copies the contents of the source directory
  into the destination directory.
  It assumes that the source and destination directories exist.
  """
  filePathList = os.listdir(srcDir)
  for filePath in filePathList:
    absFilePath = osp.join(srcDir, filePath)
    subp.run(f"cp -r {absFilePath} {destDir}", shell=True)


def copyFile(filePath: RelFilePathT, destDir: RelFilePathT) -> None:
  shutil.copy(filePath, destDir)


def renameFile(currName: str, newName: str):  # TODO: return False on failure
  os.rename(currName, newName)


def prepareDestinationDirectory(
    srcDirPath: RelFilePathT,
    destDirPath: RelFilePathT,
) -> None:
  """
  It tries to copy the contents of source directory to the
  destination directory without overwriting.
  Assumption: source directory exists.
  """
  # STEP 0: get absolute paths (optional)
  absDestDirPath: AbsFilePathT \
    = getAbolutePath(destDirPath)
  absSrcDirPath: AbsFilePathT \
    = getAbolutePath(srcDirPath)

  # STEP 1: create the destination dir if doesn't exist
  createDir(absDestDirPath)

  # STEP 2: Systematically copy the contents of source dir to destination dir
  if isEmptyDir(absDestDirPath):
    # STEP 3.1: If destination dir is empty copy the whole source dir
    copyDirectoryContents(absSrcDirPath, absDestDirPath)
  else:
    # STEP 3.2:
    # Selectively copy files if they don't exist in the destination dir
    prefixLen = len(absSrcDirPath) + 1
    for absSrcFilePath in getAllFilePaths(absSrcDirPath):
      relFilePath = absSrcFilePath[prefixLen:]  # remove prefix
      relDirPath = osp.dirname(relFilePath)
      absFilePath = osp.join(absDestDirPath, relFilePath)
      absDirPath = osp.join(absDestDirPath, relDirPath)

      if not osp.exists(absDirPath):
        createDir(absDestDirPath)

      if not osp.exists(absFilePath):
        copyFile(absSrcFilePath, absDirPath)


def getFileModTimeInNanoSecs(filePath: str) -> int:
  stat = os.stat(filePath, follow_symlinks=True)
  return stat.st_mtime_ns


def programExists(progName: str) -> bool:
  """Returns True if the given command exists."""
  cmd = f"which {progName}"
  completed = subp.run(cmd, shell=True)
  if completed.returncode != 0:
    return False
  return True


def exitIfProgramDoesnotExist(progName: str,
    exitCode: int = 1
) -> None:
  """Fails and exits if the command doesn't exist."""
  if not programExists(progName):
    print(f"ERROR: Program `{progName}` is not in path. Exiting.", file=sys.stderr)
    exit(exitCode)


################################################
# BLOCK END  : FileSystem_Related
################################################

def getUniqueId() -> int:
  """Returns a unique integer id (increments by 1)."""
  # use of simple function and a global var is runtime efficient.
  global globalCounter
  globalCounter += 1
  return globalCounter


def getUserName() -> str:
  return os.environ.get("USER", "user")


def hexToFloat(hexVal) -> float:
  """Convert a float hex representation 0x41b80000 to a real float value"""
  import struct
  if isinstance(hexVal, str):
    return struct.unpack("!f", struct.pack("!i", int(hexVal, 16)))[0]
  elif isinstance(hexVal, int):
    return struct.unpack("!f", struct.pack("!i", hexVal))[0]
  raise ValueError(f"{type(hexVal)}")


def hexToDouble(hexVal) -> float:
  """Convert a float hex representation 0x41b80000 to a real double value"""
  import struct
  if isinstance(hexVal, str):
    return struct.unpack("!d", struct.pack("!q", int(hexVal, 16)))[0]
  elif isinstance(hexVal, int):
    return struct.unpack("!d", struct.pack("!q", hexVal))[0]
  raise ValueError(f"{type(hexVal)}")


def randomString(length: int = 10,
    digits: bool = True,
    caps: bool = False,
    small: bool = True,
) -> Opt[str]:
  """Returns a random string of given length."""
  import random
  import string
  if not (digits or caps or small): return None

  size = length
  if length > 1:
    size = length // 2

  collect = []
  if digits:
    randDigits = random.choices(string.digits, k=size)
    collect = randDigits
  if caps:
    randCaps = random.choices(string.ascii_uppercase, k=size)
    collect.extend(randCaps)
  if small:
    randSmall = random.choices(string.ascii_lowercase, k=size)
    collect.extend(randSmall)

  random.shuffle(collect)
  return "".join(collect[:length])


def getLineNumFunc() -> Callable[[str, int], int]:
  """Returns a function that calculates
  the line number of the given pos in
  the string s. It optimizes by caching the last
  calculated result."""
  # used in calculation of line number
  lastStr, lastPos, lastLineCount = "", 0, 0

  def calcLineNum(s: str, pos: int) -> int:
    nonlocal lastStr, lastPos, lastLineCount
    if s != lastStr:
      lastStr = s
      lastPos = 0
      lastLineCount = 1
    for i in range(lastPos, pos):
      if s[i] == os.linesep:
        lastLineCount += 1
    return lastLineCount

  return calcLineNum


def getSize(obj, seen: Opt[Set[int]] = None) -> int:
  """Recursively finds size of objects. Needs: import sys """
  seen = set() if seen is None else seen

  if id(obj) in seen: return 0  # to handle self-referential objects
  seen.add(id(obj))

  size = sys.getsizeof(obj, 0)  # pypy3 always returns default (necessary)
  if isinstance(obj, dict):
    size += sum(getSize(v, seen) + getSize(k, seen) for k, v in obj.items())
  elif hasattr(obj, '__dict__'):  # not true if '__slots__' are used
    size += getSize(obj.__dict__, seen)
  elif hasattr(obj, '__slots__'):  # in case slots are in use
    slotList = [getattr(C, "__slots__", []) for C in obj.__class__.__mro__]
    slotList = [[slot] if isinstance(slot, str) else slot for slot in slotList]
    size += sum(getSize(getattr(obj, a, None), seen) for slot in slotList for a in slot)
  elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
    size += sum(getSize(i, seen) for i in obj)
  return size


class Timer:
  """
  A timer class used to measure time of an activity in a large project.
  It also works if functions are recursive.

  Usage:
  1. Create Timer object as: `timer = Timer()`
  2. To start use: timer.start()
  3. To stop  use: timer.stop()

  The timer truly stops if starts and stops are balanced.
  For example,
  timer.start(); timer.start();  # the second start is like a NOP
  timer.stop();  timer.stop();   # the first stop is like a NOP
  stop() calls should balance start() calls.
  """
  __slots__: List[str] = ["name", "_start", "cumulativeTime", "startCounts",
                          "stopCounts", "counter"]

  def __init__(self, name=None, start=True):
    self.name = name if name else f"Timer{getUniqueId()}"
    self._start = None
    self.cumulativeTime: float = 0  # in microseconds
    self.startCounts = 0
    self.stopCounts = 0
    self.counter = 0  # number of starts should match stops
    if start:
      self.start()

  def start(self):
    if self.counter == 0:
      self._start = time.time()
    self.counter += 1
    self.startCounts += 1

  def stop(self) -> 'Timer':
    self.counter -= 1
    if self.counter == 0:
      self.cumulativeTime += time.time() - self._start
      self.stopCounts += 1
    return self

  def stopAndLog(self) -> None:
    if LS: LOG.debug(self.stop())

  def getDurationInMillisec(self) -> float:
    return self.cumulativeTime * 1000

  def __str__(self):
    return f"TimeElapsed({self.name}):" \
           f" {self.getDurationInMillisec()} ms" \
           f" (Starts: {self.startCounts}, Stops: {self.stopCounts})"

  def __repr__(self):
    return str(self)


class CacheHits:
  """
  Keeps track of the hits of the cache.
  """

  __slots__: List[str] = ["name", "hits", "misses"]

  def __init__(self, name=""):
    self.name = name if name else f"Cache{getUniqueId()}"
    self.hits, self.misses = 0, 0

  def hit(self):
    self.hits += 1

  def miss(self):
    self.misses += 1

  def hitRatio(self) -> int:
    total = self.hits + self.misses
    return int((100 * self.hits / total) if total != 0 else 0)

  def __str__(self):
    return f"HitRatio({self.name}): {self.hitRatio()} % (hits={self.hits}, misses={self.misses})"

  def __repr__(self):
    return str(self)


def isIterable(obj) -> bool:
  """A safe check to confirm if an item is iterable."""
  try:
    iter(obj)
  except Exception:
    return False
  else:
    return True


