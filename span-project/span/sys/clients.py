#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Record the analyses listed in span.clients.register.

All properties of analyses are recorded here,
for use in the rest of the system.
"""

import logging

LOG = logging.getLogger("span")
from typing import Dict, Set, Optional as Opt, cast, Type
import io

from span.util.logger import LS
import span.clients.register as register

import span.api.sim as sim
import span.api.analysis as analysis
import span.ir.types as types

LhsVar__to__Nil__Name = sim.SimAT.LhsVar__to__Nil.__name__

# list of all concrete analysis class given
# this dictionary is used with in package span.sys only.
analyses: Dict[analysis.AnalysisNameT, type] = dict()
# record of analyses names, that implement a particular expr evaluation
# NOTE: if no analysis simplifies a particular sim func, still
# add an empty set corresponding to the key.
simSrcMap: Dict[sim.SimNameT, Set[analysis.AnalysisNameT]] = dict()
# record of blocking expressions of an analysis
simNeedMap: Dict[analysis.AnalysisNameT, Set[sim.SimNameT]] = dict()
# record analyses that also work as simplifiers
simAnalyses: Set[analysis.AnalysisNameT] = set()
# map analyses to the set of transfer functions it gives
anTFuncMap: Dict[analysis.AnalysisNameT, Set[str]] = dict()
# analyses which override FilterI instruction, and needs its simplification
anNeedsFullLiveness: Set[analysis.AnalysisNameT] = set()
# analyses which override FilterI instruction,
# and doesn't need its simplification
anNeedsLiveness: Set[analysis.AnalysisNameT] = set()


class Clients:
  """The (only) object of this class contains all client analyses names,
  as attributes."""


  def __str__(self):
    ret: str = None
    with io.StringIO() as sio:
      for name in sorted(self.__dict__):
        sio.write(f"{name} ")
      sio.write(f"\nTotal Analyses: {len(self.__dict__)}.")
      ret = sio.getvalue()
    return ret


  def __repr__(self):
    return self.__str__()


# see its use.
names = Clients()


def initGlobals():
  global analyses, simSrcMap, simNeedMap, simAnalyses
  global anTFuncMap, anNeedsLiveness, anNeedsFullLiveness

  # init analyses
  analyses = dict()

  # init evals
  simSrcMap = dict()
  for memberName in sim.simNames:
    simSrcMap[memberName] = set()

  simNeedMap = dict()
  simAnalyses = set()
  anTFuncMap = dict()
  anNeedsLiveness = set()
  anNeedsFullLiveness = set()


def recordTFunctions(anName: analysis.AnalysisNameT,
    anClass: type
) -> None:
  """Record the transfer functions provided by an analysis."""
  global anTFuncMap
  anTFuncMap[anName] = set()

  anClassMembers = anClass.__dict__
  allTFuncs = analysis.AnalysisAT.__dict__
  for memberName in anClassMembers:
    if memberName.endswith("_Instr") and memberName in allTFuncs:
      anTFuncMap[anName].add(memberName)


def recordSimsProvided(anName: analysis.AnalysisNameT,
    anClass: type
) -> None:
  """Record the simplifications provided by an analysis."""
  global simSrcMap, simAnalyses
  aSimAnalysis = False

  anClassMembers = anClass.__dict__
  for memberName in anClassMembers:
    if memberName in simSrcMap:
      simSrcMap[memberName].add(anName)
      aSimAnalysis = True

  if aSimAnalysis: simAnalyses.add(anName)


def recordSimsNeeded(anName: analysis.AnalysisNameT,
    anClass: Type[analysis.AnalysisAT],
) -> None:
  """records the blocking expressions of the given analysis."""
  global simNeedMap
  tmp = set()

  for m in anClass.simNeeded:  # simNeeded field is runtime correct
    tmp.add(m.__name__)
  simNeedMap[anName] = tmp


def recordLivenessInfoOfAn(anName: analysis.AnalysisNameT,
    anClass: Type[analysis.AnalysisAT],
) -> None:
  """Record the if analysis implements Live_Instr method"""
  global anNeedsFullLiveness, anNeedsLiveness
  overridesLiveInstr = False

  liveInstrName = analysis.AnalysisAT.Filter_Instr.__name__
  anClassMembers = anClass.__dict__
  if liveInstrName in anClassMembers:
    anNeedsLiveness.add(anName)
    overridesLiveInstr = True

  for m in anClass.simNeeded:  # simNeeded field is runtime correct
    if m.__name__ == LhsVar__to__Nil__Name and overridesLiveInstr:
      anNeedsFullLiveness.add(anName)


def getDirection(anName: analysis.AnalysisNameT
) -> Opt[types.DirectionT]:
  direction = None
  if anName in analyses:
    anClass = cast(Type[analysis.AnalysisAT], analyses[anName])
    D = anClass.D  # it must be type correct
    assert D, f"{anClass.__name__}"
    if D.__name__.startswith("Forw"):
      direction = types.Forward
    elif D.__name__.startswith("Back"):
      direction = types.Backward
    elif D.__name__.startswith("ForwBack"):
      direction = types.ForwBack
  return direction


# mainentry for this module
def init():
  global names, analyses
  initGlobals()
  for anName, anClass in register.__dict__.items():
    if type(anClass) == type:
      # so its a class... make sure its an analysis
      if issubclass(anClass, analysis.AnalysisAT):
        # okay, now do a proper book keeping of the analysis
        analyses[anName] = anClass
        recordSimsProvided(anName, anClass)
        recordSimsNeeded(anName, anClass)
        recordTFunctions(anName, anClass)
        recordLivenessInfoOfAn(anName, anClass)
        setattr(names, anName, anName)
        if LS: LOG.debug("AddedAnalysis: %s", anName)


init()

if LS: LOG.debug("Analyses: %s", analyses)
if LS: LOG.debug("SimSources: %s", simSrcMap)
if LS: LOG.debug("SimNeeds: %s", simNeedMap)
if LS: LOG.debug("SimAnalyses: %s", simAnalyses)
if LS: LOG.debug("LivenessAwareAn: %s", anNeedsFullLiveness)
