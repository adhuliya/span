#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Manages/Runs the code diagnosis subsystem."""

import logging

LOG = logging.getLogger("span")

from typing import List, Optional as Opt, Dict, Set
import io

import span.util.util as util
from span.util.util import LS

import span.api.analysis as analysis
import span.api.dfv as dfv
import span.ir.types as types
import span.ir.tunit as irTUnit
import span.ir.constructs as obj

import span.sys.host as host

import span.diagnoses.register as register
import span.api.diagnosis as diagnosis

AnalysisClassT = type

allDiagnoses: Dict[diagnosis.DiagnosisNameT,
                   diagnosis.DiagnosisClassT] = {}


# mainentry for this module
def init():
  """Add diagnoses imported in span.diagnoses.register module."""
  global allDiagnoses
  allDiagnoses = {}
  for diName, diClass in register.__dict__.items():
    if type(diClass) == type:
      if issubclass(diClass, diagnosis.DiagnosisRT):
        allDiagnoses[diName] = diClass


def runDiagnosis(diName: diagnosis.DiagnosisNameT,
    func: obj.Func,
    cascade: bool = False,
    lerner: bool = False,
) -> Opt[List[diagnosis.Report]]:
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

  diObj: diagnosis.DiagnosisRT = DiClass()

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
                Dict[types.NodeIdT, dfv.NodeDfvL]] = {}

  anResults = syn1.getAnalysisResults(anName).nidNdfvMap
  assert anResults, f"{anName}"
  results[anName] = anResults
  if diObj.OptionalNeeds:
    for an in diObj.OptionalNeeds:
      anResults = syn1.getAnalysisResults(an.__name__).nidNdfvMap
      assert anResults, f"{anName}"
      results[an.__name__] = anResults

  reports = diObj.handleResults(results, func)

  return reports
