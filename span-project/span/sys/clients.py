#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""Record the analyses listed in span.clients.register.

All properties of analyses are recorded here,
for use in the rest of the system.
"""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from typing import Dict, Set, Optional as Opt, cast, Type, TypeVar, Tuple
import io
import functools

import span.clients.register as register
import span.util.util as util
from span.ir.constructs import Func

import span.ir.conv as irConv
from span.api.analysis import (
  AnNameT, AnalysisAT, SimNameT, SimNames,
  DirectionDT, ForwardD, BackwardD, AnalysisAT_T,
  Deref__to__Vars__Name, Num_Var__to__Num_Lit__Name, LhsVar__to__Nil__Name,
  Num_Bin__to__Num_Lit__Name, Cond__to__UnCond__Name, Node__to__Nil__Name,
)
import span.ir.types as types

# list of all concrete analysis class given
# this dictionary is used with in package span.sys only.
analyses: Dict[AnNameT, Type[AnalysisAT_T]] = dict()
# record of analyses names, that implement a particular expr evaluation
# NOTE: if no analysis simplifies a particular sim func, still
# add an empty set corresponding to the key.
simSrcMap: Dict[SimNameT, Set[AnNameT]] = dict()
# record of blocking expressions of an analysis
simNeedMap: Dict[AnNameT, Set[SimNameT]] = dict()
# record analyses that also work as simplifiers
simAnalyses: Set[AnNameT] = set()
# map analyses to the set of transfer functions it gives
anTFuncMap: Dict[AnNameT, Set[str]] = dict()
# analyses which override FilterI instruction, and needs its simplification
anReadyForLivenessSim: Set[AnNameT] = set()
# analyses which override FilterI instruction,
# and doesn't need its simplification
anAcceptingLivenessSim: Set[AnNameT] = set()

# memoized analysis' instance for specific functions
_anObjMap: Dict[Tuple[AnNameT, types.FuncNameT], AnalysisAT] = dict()


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


# see its use -- not used anymore
names: Clients = Clients()


def initGlobals():
  global analyses, simSrcMap, simNeedMap, simAnalyses
  global anTFuncMap, anAcceptingLivenessSim, anReadyForLivenessSim

  # init analyses
  analyses = dict()

  # init evals
  simSrcMap = dict()
  for memberName in SimNames:
    simSrcMap[memberName] = set()

  simNeedMap = dict()
  simAnalyses = set()
  anTFuncMap = dict()
  anAcceptingLivenessSim = set()
  anReadyForLivenessSim = set()


def recordTFunctions(anName: AnNameT,
    anClass: type
) -> None:
  """Record the transfer functions provided by an analysis."""
  global anTFuncMap
  anTFuncMap[anName] = set()

  anClassMembers = anClass.__dict__
  allTFuncs = AnalysisAT.__dict__
  for memberName in anClassMembers:
    if memberName.endswith("_Instr") and memberName in allTFuncs:
      anTFuncMap[anName].add(memberName)


def recordSimsProvided(anName: AnNameT,
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


def recordSimsNeeded(anName: AnNameT,
    anClass: Type[AnalysisAT],
) -> None:
  """records the blocking expressions of the given analysis."""
  global simNeedMap
  tmp = set()

  for simName in getSimNamesNeeded(anClass):  # simNeeded field is runtime correct
    tmp.add(simName)
  simNeedMap[anName] = tmp


def recordLivenessInfoOfAn(anName: AnNameT,
    anClass: Type[AnalysisAT],
) -> None:
  """Record the if analysis implements Live_Instr method"""
  global anReadyForLivenessSim, anAcceptingLivenessSim
  overridesLiveInstr = False

  liveInstrName = AnalysisAT.LiveLocations_Instr.__name__
  anClassMembers = anClass.__dict__
  if liveInstrName in anClassMembers:
    anAcceptingLivenessSim.add(anName)
    overridesLiveInstr = True

  for simName in getSimNamesNeeded(anClass):  # simNeeded field is runtime correct
    if simName == LhsVar__to__Nil__Name and overridesLiveInstr:
      anReadyForLivenessSim.add(anName)


def getSimNamesNeeded(anClass: Type[AnalysisAT]) -> Set[str]:
  """Returns the names of sim needed by the analyses."""
  simNames = set()

  if anClass.needsRhsDerefToVarsSim:
    simNames.add(Deref__to__Vars__Name)
  if anClass.needsLhsDerefToVarsSim:
    simNames.add(Deref__to__Vars__Name)
  if anClass.needsNumVarToNumLitSim:
    simNames.add(Num_Var__to__Num_Lit__Name)
  if anClass.needsNumBinToNumLitSim:
    simNames.add(Num_Bin__to__Num_Lit__Name)
  if anClass.needsCondToUnCondSim:
    simNames.add(Cond__to__UnCond__Name)
  if anClass.needsLhsVarToNilSim:
    simNames.add(LhsVar__to__Nil__Name)
  if anClass.needsNodeToNilSim:
    simNames.add(Node__to__Nil__Name)
  if anClass.needsFpCallSim:
    simNames.add(Deref__to__Vars__Name)

  return simNames


@functools.lru_cache(32)
def getAnClass(anName: AnNameT
) -> Opt[Type[AnalysisAT_T]]:
  if anName in analyses:
    return analyses[anName]
  raise ValueError(f"UnknownAnalysis: {anName}")


@functools.lru_cache(32)
def getAnDirn(anName: AnNameT
) -> Opt[types.DirectionT]:
  if anName in analyses:
    anClass = cast(Type[AnalysisAT], analyses[anName])
    return anClass.D  # it must be type correct
  raise ValueError(f"UnknownAnalysis: {anName}")


def getAnObj(anName: AnNameT, func: Func) -> AnalysisAT:
  """Returns an basic object of analysis instantiated
   for the given function, and caches the result.
   Hence, DON'T modify the objects.

   Use this function only to call the sim functions that
   can only be called on the analysis objects for now.
   """
  tup = (anName, func.name)
  if tup in _anObjMap:
    return _anObjMap[tup]
  else:
    anObj = _anObjMap[tup] = getAnClass(anName)(func)
    return anObj


@functools.lru_cache(32)
def getAnDirnClass(anName: AnNameT
) -> Type[DirectionDT]:
  dirn = getAnDirn(anName)
  if dirn == irConv.Forward:
    return ForwardD
  elif dirn == irConv.Backward:
    return BackwardD
  elif dirn == irConv.ForwBack:
    raise ValueError(f"Handled ForwBack direction yet?")
    # return ForwBackDT
  raise ValueError(f"UnknownDirection: {anName}, {dirn}")


def isAnPresent(anName: AnNameT) -> bool:
  """Is the given analysis name present in the system?"""
  return anName in analyses


# mainentry for this module
def init():
  global names, analyses
  initGlobals()
  for anName, anClass in register.__dict__.items():
    if type(anClass) == type:
      # so its a class... make sure its an analysis
      if issubclass(anClass, AnalysisAT):
        # okay, now do a proper book keeping of the analysis
        analyses[anName] = anClass
        recordSimsProvided(anName, anClass)
        recordSimsNeeded(anName, anClass)
        recordTFunctions(anName, anClass)
        recordLivenessInfoOfAn(anName, anClass)
        setattr(names, anName, anName)
        if util.LL1: LDB("AddedAnalysis: %s", anName)


################################################################################
init() ## INITIALIZE TO USE THE CLIENTS ########################################
################################################################################


if util.LL1: LDB("Analyses: %s", analyses)
if util.LL1: LDB("SimSources: %s", simSrcMap)
if util.LL1: LDB("SimNeeds: %s", simNeedMap)
if util.LL1: LDB("SimAnalyses: %s", simAnalyses)
if util.LL1: LDB("LivenessAwareAn: %s", anReadyForLivenessSim)


