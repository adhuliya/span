#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Manages/Runs the code diagnosis subsystem."""

import logging

from span.sys import clients

LOG = logging.getLogger(__name__)

from typing import List, Optional as Opt, Dict, Set, Type
import io

import span.util.util as util
from span.util.util import LS

import span.api.analysis as analysis
import span.api.dfv as dfv
import span.ir.types as types
import span.ir.tunit as irTUnit
from span.ir.constructs import Func

import span.sys.host as host

import span.diagnoses.register as register
from span.api.diagnosis import (
  MethodT, DiagnosisNameT, DiagnosisClassT, DiagnosisRT, Report,
)

AnalysisClassT = type

allDiagnoses: Dict[DiagnosisNameT, DiagnosisClassT] = {}


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
) -> Opt[List[Report]]:
  """Runs the given dianosis and returns a list of reports.
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

  anName: analysis.AnalysisNameT = diObj.Needs[0].__name__

  if cascade:
    syn1 = host.Host(func, analysisSeq=diObj.AnalysesSeqCascading)
  elif lerner:
    syn1 = host.Host(func, analysisSeq=diObj.AnalysesSeqLerner)
  else:
    syn1 = host.Host(func, anName,
                     otherAnalyses=[an.__name__ for an in diObj.OptionalNeeds])
  syn1.analyze()  # do the analysis
  # AD syn1.printResult() # print the result of each analysis

  results: Dict[analysis.AnalysisNameT,
                Dict[types.NodeIdT, dfv.DfvPairL]] = {}

  anResults = syn1.getAnalysisResults(anName).anResult.result
  assert anResults, f"{anName}"
  results[anName] = anResults
  if diObj.OptionalNeeds:
    for an in diObj.OptionalNeeds:
      anResults = syn1.getAnalysisResults(an.__name__).anResult.result
      assert anResults, f"{anName}"
      results[an.__name__] = anResults

  reports = diObj.handleResults(results, func)

  return reports


def runDiagnosisNew(
    diName: DiagnosisNameT,
    func: Func,
    methodName: Opt[MethodT],
) -> Opt[List[Report]]:
  """Runs the given dianosis and returns a list of reports.
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

  DiClass = allDiagnoses[diName] # get the diagnosis class

  diObj: DiagnosisRT = DiClass()

  for methodDetails in diObj.MethodSequence: # run each method
    if methodName and methodDetails.methodName != methodName:
      continue

    try: # try loading the analyses
      anClassMap = loadAnalyses(methodDetails.anNames)
    except ValueError: # failed? Then don't proceed.
      continue

    for config in methodDetails.configSeq: # run each config of the method
      res = diObj.computeResults(methodDetails.methodName, config, anClassMap)
      diObj.handleResults(res, anClassMap)


def loadAnalyses(anNames: List[types.AnNameT]):
  """Loads the class of the given analysis names.

  It throws ValueError, if the Analysis Name is not found.
  """
  anClassMap: Dict[types.AnNameT, Type[AnalysisClassT]] = {}

  for anName in anNames:
    anClass = clients.getAnClass(anName) # may throw ValueError
    anClassMap[anName] = anClass

  return anClassMap

