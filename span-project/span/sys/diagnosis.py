#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""Manages/Runs the code diagnosis subsystem."""

import logging
LOG = logging.getLogger(__name__)

from span.sys import clients

from typing import List, Optional as Opt, Dict, Set, Type
import io

import span.util.util as util
from span.util.util import LS, Timer

from span.api.analysis import (
  AnalysisAT_T,
)
from span.api.dfv import DfvPairL
from span.ir.types import (
  AnNameT, NodeIdT, FileNameT,
)
import span.ir.tunit as irTUnit
from span.ir.constructs import Func

import span.sys.host as host

import span.diagnoses.register as register
from span.api.diagnosis import (
  MethodT, DiagnosisNameT, DiagnosisRClassT, DiagnosisRT, ClangReport, UseAllMethods,
)

AnalysisClassT = type

allDiagnoses: Dict[DiagnosisNameT, Type[DiagnosisRClassT]] = {}


# mainentry for this module
def init():
  """Add diagnoses imported in span.diagnoses.register module."""
  global allDiagnoses
  allDiagnoses = {}
  for diName, diClass in register.__dict__.items():
    if type(diClass) == type:
      if issubclass(diClass, DiagnosisRT):
        allDiagnoses[diName] = diClass


def runDiagnosis(diName: DiagnosisNameT,
    func: Func,
    cascade: bool = False,
    lerner: bool = False,
) -> Opt[List[ClangReport]]:
  """Runs the given diagnosis and returns a list of reports.
  The reports can be read in by a clang checker developed for this purpose.
  To view the checkers in clang see:
    clang -cc1 -analyzer-checker-help-developer
  But this might not show the debug.* checkers on newer versions.
  So view the following checkers file to see the complete list:
    Assuming clang's build/ directory is in the same location as
    source llvm directory then view Checkers.td as follows:
      vi "$(dirname $(which clang))/../../llvm/tools/clang/include/clang/StaticAnalyzer/Checkers/Checkers.td"
  """
  if LS: LOG.debug("DiagnosingFunction: %s", func.name)
  # get diagnosis class
  DiClass = allDiagnoses[diName]

  diObj: DiagnosisRT = DiClass()

  anName: AnNameT = diObj.Needs[0].__name__

  if cascade:
    syn1 = host.Host(func, analysisSeq=diObj.AnalysesSeqCascading)
  elif lerner:
    syn1 = host.Host(func, analysisSeq=diObj.AnalysesSeqLerner)
  else:
    syn1 = host.Host(func, anName,
                     otherAnalyses=[an.__name__ for an in diObj.OptionalNeeds])
  syn1.analyze()  # do the analysis
  # AD syn1.printResult() # print the result of each analysis

  results: Dict[AnNameT, Dict[NodeIdT, DfvPairL]] = {}

  anResults = syn1.getAnalysisResults(anName).result
  assert anResults, f"{anName}"
  results[anName] = anResults
  if diObj.OptionalNeeds:
    for an in diObj.OptionalNeeds:
      anResults = syn1.getAnalysisResults(an.__name__).result
      assert anResults, f"{anName}"
      results[an.__name__] = anResults

  reports = diObj.handleResults(results, func)

  return reports


def runDiagnosisNew(
    diName: DiagnosisNameT,
    diMethod: MethodT,
    configId: int,
    fileName: FileNameT,
    tUnit: irTUnit.TranslationUnit,
) -> None:
  """Runs the given diagnosis and returns a list of reports.
  The reports can be read in by a clang checker developed for this purpose.
  To view the checkers in clang see:
    clang -cc1 -analyzer-checker-help-developer
  But this might not show the debug.* checkers on newer versions.
  So view the following checkers file to see the complete list:
    Assuming clang's build/ directory is in the same location as
    source llvm directory then view Checkers.td as follows:
      vi "$(dirname $(which clang))/../../llvm/tools/clang/include/clang/StaticAnalyzer/Checkers/Checkers.td"
  """
  if LS: LOG.debug("RunningDiagnosis: DiName: %s, DiMethod: %s,"
                   "configId: %s, fileName: %s",
                   diName, diMethod, configId, fileName)

  DiClass = allDiagnoses[diName] # get the diagnosis class

  diObj: DiagnosisRT = DiClass(tUnit)

  #STEP 1: Iterate over each method.
  for mDetails in diObj.MethodSequence: # run each method
    if (diMethod
        and diMethod != mDetails.name
        and diMethod != UseAllMethods
    ):
      # if diMethod is given, skip undesirable methods
      continue

    #STEP 1.5: Load analyses. Don't proceed if analyses not present.
    try: # try loading the analyses
      anClassMap = loadAnalyses(mDetails.anNames)
    except ValueError as e: # failed? Then don't proceed.
      print(f"SomeAnalysesNotPresentIn: {mDetails.anNames}"
            f" (ErrorMsg: '{e.args[0]}')")
      continue

    #STEP 2: COMPUTE.
    timer = Timer(f"{mDetails.name}:{mDetails.subName}")
    diObj.init(mDetails, anClassMap)
    dfvs = diObj.computeDfvs(mDetails, anClassMap)
    if dfvs: # could be None
      res = diObj.computeResults(mDetails, dfvs, anClassMap)
      diObj.handleResults(mDetails, res, dfvs, anClassMap)
    diObj.finish(mDetails, anClassMap)
    timer.stopAndLog(printAlso=True)


def loadAnalyses(
    anNames: List[AnNameT]
) -> Dict[AnNameT, Type[AnalysisAT_T]]:
  """Loads the class of the given analysis names.

  It throws ValueError, if an Analysis' Name is not found.
  """
  anClassMap: Dict[AnNameT, Type[AnalysisAT_T]] = {}

  for anName in anNames:
    anClass = clients.getAnClass(anName) #NOTE: May throw ValueError.
    anClassMap[anName] = anClass

  return anClassMap

