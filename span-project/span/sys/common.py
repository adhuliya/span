#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Common functionality needed by other sys modules.
"""

import logging

from span.ir.types import FuncNameT, FuncNodeIdT, NodeIdT, FuncIdT

LOG = logging.getLogger("span")
LDB, LIN = LOG.debug, LOG.info

from typing import Dict, Tuple, Set, List, cast, Optional as Opt

import span.sys.clients as clients
from span.ir.conv import Forward, Backward, getFuncNodeIdStr, getNodeId, getFuncId
from span.api.analysis import AnalysisNameT as AnNameT
from span.api.dfv import NodeDfvL

import span.util.ff as ff
import span.util.util as util


class CallSitePair:
  """Pair of call site and function name.
  Useful in recording function name with callsite
  specially when its a function pointer based call.
  """

  __slots__ = ["callSite", "funcName"]


  def __init__(self,
      funcName: FuncNameT,
      callSite: FuncNodeIdT,
  ) -> None:
    self.funcName = funcName
    self.callSite = callSite


  def getNodeId(self) -> NodeIdT:
    return getNodeId(self.callSite)


  def __lt__(self, other):
    isLt = False
    if self.funcName < other.funcName:
      isLt = True
    elif self.funcName == other.funcName:
      if self.callSite < other.callSite:
        isLt = True
    return isLt


  def __eq__(self, other):
    if self is other: return True
    equal = True
    if not isinstance(other, CallSitePair):
      equal = False
    elif not self.callSite == other.callSite:
      equal = False
    elif not self.funcName == other.funcName:
      equal = False
    return equal


  def __hash__(self):
    return hash((self.callSite, self.funcName))


  def __str__(self):
    return f"Site({self.funcName}, {getFuncNodeIdStr(self.callSite)})"


  def __repr__(self): return self.__str__()


  def tuple(self) -> Tuple[FuncNameT, FuncNodeIdT]:
    return self.funcName, self.callSite


  def getFuncId(self) -> FuncIdT:
    return getFuncId(self.callSite)


class DfvDict:
  """A dictionary to store the: Dict[AnNameT, NodeDfvL] info.
  Along with many convenience functions to operate on the dict.
  """

  __slots__ = ["dfvs", "depth"]

  def __init__(self,
      dfvs: Opt[Dict[AnNameT, NodeDfvL]] = None,
      depth: int = 0, # useful when using widening
  ):
    self.dfvs = dfvs if dfvs else {}
    self.depth = depth


  def setIncDepth(self, other: 'DfvDict'):
    self.depth = other.depth + 1


  def setValue(self,
      anName: AnNameT,
      nDfv: NodeDfvL,
  ) -> None:
    self.dfvs[anName] = nDfv


  def getCopy(self):
    return DfvDict({k: v.getCopy() for k, v in self.dfvs.items()}, self.depth)


  def getCopyShallow(self):
    return DfvDict(self.dfvs.copy(), self.depth)


  def __contains__(self, anName: AnNameT):
    return anName in self.dfvs


  def __iter__(self):
    return iter(self.dfvs.items())


  def __getitem__(self, anName: AnNameT):
    return self.dfvs[anName]


  def __setitem__(self, key: AnNameT, val: NodeDfvL):
    self.dfvs[key] = val


  def __eq__(self, other):
    if self is other: return True
    equal = True
    if not isinstance(other, DfvDict):
      equal = False
    elif not self.depth == other.depth:
      equal = False
    elif not self.dfvs.keys() == other.dfvs.keys():
      equal = False
    else:
      for anName, nDfvSelf in self.dfvs.items():
        direction = clients.getAnDirn(anName)
        nDfvOther = other[anName]
        if nDfvOther is None:
          equal = False
        elif direction == Forward:
          if not nDfvSelf.dfvIn == nDfvOther.dfvIn:
            equal = False
        elif direction == Backward:
          if not nDfvSelf.dfvOut == nDfvOther.dfvOut:
            equal = False
        else:  # bi-directional
          if not nDfvSelf == nDfvOther:
            equal = False

    return equal


  def __hash__(self) -> int:
    theHash = hash(self.depth)

    for anName, nDfv in self.dfvs.items():
      direction = clients.getAnDirn(anName)
      if direction == Forward:
        theHash = hash((theHash, nDfv.dfvIn))
      elif direction == Backward:
        theHash = hash((theHash, nDfv.dfvOut))
      else:  # bi-directional
        theHash = hash((theHash, nDfv))

    return theHash


  def __str__(self):
    idStr = "" if not util.VV5 else f"(id:{id(self)})"
    return f"DfvDict(Depth:{self.depth}," \
           f" {sorted(self.dfvs.items(), key=lambda x: x[0])}{idStr}"


  def __repr__(self): return self.__str__()



