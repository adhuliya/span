#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Testing related definitions used in the other testing
files in this package.
"""

import subprocess as subp
import unittest
from typing import List, Dict, Any

from span.api.analysis import AnalysisNameT
from span.api.diagnosis import DiagnosisNameT
import span.util.common_util as cutil
import span.ir.ir as ir
import span.util.data as data

# IMPORTANT imports for eval() to work
from span.ir.types import Loc, Info
import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.constructs as constructs
import span.ir.tunit as tunit
import span.api.dfv as dfv

# IMPORTANT imports for analyses/diagnoses
import span.clients.pointsto as pointsto
import span.clients.const as const
import span.clients.evenodd as evenodd
import span.clients.stronglive as liveness
import span.clients.interval as interval

TestFileName = str
ResultFileName = str


class TestActionAndResult:
  """
  Represents the test action to be taken,
  and the results to be expected in a single unit.
  The C file on which the action is to be invoked,
  is embedded in the file name this class' object
  is created in.
  """


  def __init__(self,
      action: str,
      analyses: List[AnalysisNameT],
      diagnoses: List[DiagnosisNameT],
      results: Dict[str, Any],
  ):
    self.action = action
    self.analyses = analyses
    self.diagnoses = diagnoses
    self.results = results


class FilePair:
  """Test file name and its results file."""


  def __init__(self,
      testFile: str,
      resultFile: str
  ) -> None:
    self.testFile = testFile
    self.resultFile = resultFile


def genTranslationUnit(cFileName: str) -> ir.TranslationUnit:
  """Generates the translation unit and returns it as a python object."""
  return ir.genTranslationUnit(cFileName)


def genFileMap(testCase: unittest.TestCase) -> Dict[TestFileName, ResultFileName]:
  """Maps the .c files to their .c.results.py files.
  A .c file with no corresponding .c.results.py file is silently avoided."""

  # get all the test c files
  status, cFiles = subp.getstatusoutput("ls spanTest[0-9][0-9][0-9].c")
  testCase.assertEqual(status, 0, data.FAIL_C_TEST_FILES_NOT_PRESENT)

  fileMap: Dict[TestFileName, ResultFileName] = dict()
  cFileList = cFiles.split()
  for cFile in cFileList:
    fileMap[cFile] = ""

  # get all result files
  suffix = ".results.py"
  status, pyFiles = subp.getstatusoutput(f"ls spanTest[0-9][0-9][0-9].c{suffix}")
  testCase.assertEqual(status, 0, data.FAIL_C_RESULT_FILES_NOT_PRESENT)

  pyFileList = pyFiles.split()
  for pyFile in pyFileList:
    if pyFile[:-(len(suffix))] in fileMap:
      fileMap[pyFile[:-(len(suffix))]] = pyFile

  # clear all .c files with no result file
  cFilesWithNoResultFile = [cFile for cFile, pyFile in fileMap.items() if not pyFile]
  for cFile in cFilesWithNoResultFile:
    del fileMap[cFile]

  return fileMap


def evalTestCaseFile(pyFileName: str) -> List[TestActionAndResult]:
  """Reads the content of the python .c.results.py files."""
  pyFileContent = cutil.readFromFile(pyFileName)
  pyFileActions: List[TestActionAndResult] = eval(pyFileContent)
  return pyFileActions
