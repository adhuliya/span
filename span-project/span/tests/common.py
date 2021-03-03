#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Testing related definitions used in the other testing
files in this package.
"""

import subprocess as subp
import unittest
from typing import List, Dict, Any, Optional as Opt

from span.api.analysis import AnalysisNameT
from span.api.diagnosis import DiagnosisNameT
import span.util.common_util as cutil
import span.ir.ir as ir
import span.util.consts as consts

TestFileName = str
ResultFileName = str

SPANIR_TEST_FILE_SUFFIX=".spanir.test.py" # example: test.c.spanir.test.py

################################################################################
## GLOBAL_FLAGS ################################################################
################################################################################
SPAN_LLVM_AVAILABLE = True
################################################################################

class TestActionAndResult:
  """
  Represents the test action to be taken,
  and the results to be expected in a single unit.
  The C file on which the action is to be invoked,
  is embedded in the file name this class' object
  is created in.
  """


  def __init__(self,
      action: str, # generally a commmand line sub-command
      analysesExpr: Opt[str] = None, # E.g.: /+LiveVarsA+PointsToA/
      diagnoses: Opt[List[DiagnosisNameT]] = None,
      results: Opt[Dict[str, Any]] = None,
      cascade: Opt[List[List[AnalysisNameT]]] = None,
      ipaEnabled: bool = False,
      ddmEnabled: bool = False,
      simDisabled: bool = False,
  ):
    self.action = action
    self.analysesExpr = analysesExpr
    self.diagnoses = diagnoses
    self.results = results
    self.cascade = cascade
    self.ipaEnabled = ipaEnabled
    self.ddmEnabled = ddmEnabled
    self.simDisabled = simDisabled


def genTranslationUnit(cFileName: str) -> ir.TranslationUnit:
  """Generates the translation unit and returns it as a python object."""
  return ir.genTranslationUnit(cFileName)


def genFileMap(testCase: unittest.TestCase) -> Dict[TestFileName, ResultFileName]:
  """Maps the .c files to their .c.results.py files.
  A .c file with no corresponding .c.results.py file is silently avoided."""

  # get all the test c files
  status, cFiles = subp.getstatusoutput("ls spanTest[0-9][0-9][0-9].c")
  testCase.assertEqual(status, 0, consts.FAIL_C_TEST_FILES_NOT_PRESENT)

  fileMap: Dict[TestFileName, ResultFileName] = dict()
  cFileList = cFiles.split()
  for cFile in cFileList:
    fileMap[cFile] = ""

  # get all result files
  suffix = ".results.py"
  status, pyFiles = subp.getstatusoutput(f"ls spanTest[0-9][0-9][0-9].c{suffix}")
  testCase.assertEqual(status, 0, consts.FAIL_C_RESULT_FILES_NOT_PRESENT)

  pyFileList = pyFiles.split()
  for pyFile in pyFileList:
    if pyFile[:-(len(suffix))] in fileMap:
      fileMap[pyFile[:-(len(suffix))]] = pyFile

  # clear all .c files with no result file
  cFilesWithNoResultFile = [cFile for cFile, pyFile in fileMap.items() if not pyFile]
  for cFile in cFilesWithNoResultFile:
    del fileMap[cFile]

  return fileMap


def genFileMapSpanir(testCase: unittest.TestCase) -> Dict[TestFileName, ResultFileName]:
  """Maps the *.c file to its *.c.spanir.test.py file.
  A .c file with no corresponding .c.spanir.test.py file is silently avoided."""

  # get all the test c files
  status, cFiles = subp.getstatusoutput("ls spanTest[0-9][0-9][0-9].c")
  testCase.assertEqual(status, 0, consts.FAIL_C_TEST_FILES_NOT_PRESENT)

  fileMap: Dict[TestFileName, ResultFileName] = dict()
  cFileList = cFiles.split()
  for cFile in cFileList:
    fileMap[cFile] = ""

  # get all result files
  suffix = SPANIR_TEST_FILE_SUFFIX
  status, irFiles = subp.getstatusoutput(f"ls spanTest[0-9][0-9][0-9].c{suffix}")
  testCase.assertEqual(status, 0, consts.FAIL_C_RESULT_FILES_NOT_PRESENT)

  irFileNameList = irFiles.split()
  for irFileName in irFileNameList:
    cFileName = irFileName[:-(len(suffix))]
    if cFileName in fileMap:
      fileMap[cFileName] = irFileName

  # clear all .c files with no result file
  cFilesWithNoResultFile = [cFile for cFile, irFile in fileMap.items() if not irFile]
  for cFile in cFilesWithNoResultFile:
    del fileMap[cFile]

  return fileMap


def evalTestCaseFile(pyFileName: str) -> List[TestActionAndResult]:
  """Reads the content of the python .c.results.py files."""
  # IMPORTANT imports for eval() to work
  from span.ir.types import Loc, Info
  import span.ir.types as types
  import span.ir.op as op
  import span.ir.expr as expr
  import span.ir.instr as instr
  import span.ir.constructs as constructs
  import span.ir.tunit as tunit
  import span.api.dfv as dfv

  pyFileContent = cutil.readFromFile(pyFileName)
  pyFileActions: List[TestActionAndResult] = eval(pyFileContent)
  return pyFileActions


