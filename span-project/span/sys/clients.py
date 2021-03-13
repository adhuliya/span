#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Record the analyses listed in span.clients.register.

All properties of analyses are recorded here,
for use in the rest of the system.
"""

import logging
LOG = logging.getLogger("span")

from typing import Dict, Set, Optional as Opt, cast, Type, TypeVar
import io
import functools

from span.util.util import LS
import span.clients.register as register

import span.ir.conv as irConv
import span.api.analysis as analysis
import span.ir.types as types

LhsVar__to__Nil__Name = analysis.AnalysisAT.LhsVar__to__Nil.__name__

AnAT = TypeVar('AnAT', bound=analysis.AnalysisAT)

# list of all concrete analysis class given
# this dictionary is used with in package span.sys only.
analyses: Dict[analysis.AnalysisNameT, Type[AnAT]] = dict()
# record of analyses names, that implement a particular expr evaluation
# NOTE: if no analysis simplifies a particular sim func, still
# add an empty set corresponding to the key.
simSrcMap: Dict[analysis.SimNameT, Set[analysis.AnalysisNameT]] = dict()
# record of blocking expressions of an analysis
simNeedMap: Dict[analysis.AnalysisNameT, Set[analysis.SimNameT]] = dict()
# record analyses that also work as simplifiers
simAnalyses: Set[analysis.AnalysisNameT] = set()
# map analyses to the set of transfer functions it gives
anTFuncMap: Dict[analysis.AnalysisNameT, Set[str]] = dict()
# analyses which override FilterI instruction, and needs its simplification
anReadyForLivenessSim: Set[analysis.AnalysisNameT] = set()
# analyses which override FilterI instruction,
# and doesn't need its simplification
anAcceptingLivenessSim: Set[analysis.AnalysisNameT] = set()


class Clients:
  """The (only) object of this class contains all client analyses names,
  as attributes."""


  def __str__(self):
    with io.StringIO() as sio:
      for name in sorted(self.__dict__):
        sio.write(f"{name} ")
      sio.write(f"\nTotal Analyses: {len(self.__dict__)}.")
      ret = sio.getvalue()
    return ret


  def __repr__(self):
    return self.__str__()


# see its use.
names: Clients = Clients()


def initGlobals():
  global analyses, simSrcMap, simNeedMap, simAnalyses
  global anTFuncMap, anAcceptingLivenessSim, anReadyForLivenessSim

  # init analyses
  analyses = dict()

  # init evals
  simSrcMap = dict()
  for memberName in analysis.simNames:
    simSrcMap[memberName] = set()

  simNeedMap = dict()
  simAnalyses = set()
  anTFuncMap = dict()
  anAcceptingLivenessSim = set()
  anReadyForLivenessSim = set()


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

  for simName in getSimNamesNeeded(anClass):  # simNeeded field is runtime correct
    tmp.add(simName)
  simNeedMap[anName] = tmp


def recordLivenessInfoOfAn(anName: analysis.AnalysisNameT,
    anClass: Type[analysis.AnalysisAT],
) -> None:
  """Record the if analysis implements Live_Instr method"""
  global anReadyForLivenessSim, anAcceptingLivenessSim
  overridesLiveInstr = False

  liveInstrName = analysis.AnalysisAT.Filter_Instr.__name__
  anClassMembers = anClass.__dict__
  if liveInstrName in anClassMembers:
    anAcceptingLivenessSim.add(anName)
    overridesLiveInstr = True

  for simName in getSimNamesNeeded(anClass):  # simNeeded field is runtime correct
    if simName == LhsVar__to__Nil__Name and overridesLiveInstr:
      anReadyForLivenessSim.add(anName)


def getSimNamesNeeded(anClass: Type[analysis.AnalysisAT]) -> Set[str]:
  """Returns the names of sim needed by the analyses."""
  simNames = set()

  if anClass.needsRhsDerefToVarsSim:
    simNames.add(analysis.Deref__to__Vars__Name)
  if anClass.needsLhsDerefToVarsSim:
    simNames.add(analysis.Deref__to__Vars__Name)
  if anClass.needsNumVarToNumLitSim:
    simNames.add(analysis.Num_Var__to__Num_Lit__Name)
  if anClass.needsNumBinToNumLitSim:
    simNames.add(analysis.Num_Bin__to__Num_Lit__Name)
  if anClass.needsCondToUnCondSim:
    simNames.add(analysis.Cond__to__UnCond__Name)
  if anClass.needsLhsVarToNilSim:
    simNames.add(analysis.LhsVar__to__Nil__Name)
  if anClass.needsNodeToNilSim:
    simNames.add(analysis.Node__to__Nil__Name)
  if anClass.needsFpCallSim:
    simNames.add(analysis.Deref__to__Vars__Name)

  return simNames


@functools.lru_cache(32)
def getAnClass(anName: analysis.AnalysisNameT
) -> Opt[Type[AnAT]]:
  if anName in analyses:
    return analyses[anName]
  raise ValueError(f"UnknownAnalysis: {anName}")


@functools.lru_cache(32)
def getAnDirection(anName: analysis.AnalysisNameT
) -> Opt[types.DirectionT]:
  if anName in analyses:
    anClass = cast(Type[analysis.AnalysisAT], analyses[anName])
    return anClass.D  # it must be type correct
  raise ValueError(f"UnknownAnalysis: {anName}")


@functools.lru_cache(32)
def getAnDirnClass(anName: analysis.AnalysisNameT
) -> Type[analysis.DirectionDT]:
  dirn = getAnDirection(anName)
  if dirn == irConv.Forward:
    return analysis.ForwardD
  elif dirn == irConv.Backward:
    return analysis.BackwardD
  elif dirn == irConv.ForwBack:
    raise ValueError(f"Handled ForwBack direction yet?")
    # return analysis.ForwBackDT
  raise ValueError(f"UnknownDirection: {anName}, {dirn}")


def isAnalysisPresent(anName: analysis.AnalysisNameT) -> bool:
  """Is the given analysis name present in the system?"""
  return anName in analyses


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
if LS: LOG.debug("LivenessAwareAn: %s", anReadyForLivenessSim)
