#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Common functionality needed by other sys modules.
"""
import logging
_LOG = logging.getLogger(__name__)
LDB, LIN = _LOG.debug, _LOG.info

import io
from typing import Dict, Tuple, Set, List, cast, Optional as Opt

from span.ir.constructs import Func
import span.sys.clients as clients
from span.ir.conv import Forward, Backward, getGlobalNodeIdStr, getNodeId, getFuncId
from span.ir.types import FuncNameT, GlobalNodeIdT, NodeIdT, FuncIdT
from span.api.analysis import AnalysisNameT as AnNameT
from span.api.dfv import DfvPairL

import span.util.util as util


class CalleeAndCallSite:
  """A pair of function name (callee) and the call site.
  Useful in associating function name with call site,
  especially when its a function pointer based call.
  """

  __slots__ = ["callSite", "funcName"]


  def __init__(self,
      funcName: FuncNameT, # callee name called from the call site
      callSite: GlobalNodeIdT,
  ) -> None:
    self.funcName = funcName
    self.callSite = callSite


  def getFuncId(self) -> FuncIdT:
    return getFuncId(self.callSite)


  def getNodeId(self) -> NodeIdT:
    return getNodeId(self.callSite)


  def tuple(self) -> Tuple[FuncNameT, GlobalNodeIdT]:
    return self.funcName, self.callSite


  def __lt__(self, other):
    """Used for sorting a collection."""
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
    if not isinstance(other, CalleeAndCallSite):
      equal = False
    elif not self.callSite == other.callSite:
      equal = False
    elif not self.funcName == other.funcName:
      equal = False
    return equal


  def __hash__(self):
    return hash((self.funcName, self.callSite))


  def __str__(self):
    return f"Site({self.funcName}, {getGlobalNodeIdStr(self.callSite)})"


  def __repr__(self): return self.__str__()


class AnDfvPairDict:
  """A dictionary to store the: Dict[AnNameT, DfvPairL] info.

  Along with many convenience functions to operate on the dict.
  """

  __slots__ = ["dfvs", "depth"]

  def __init__(self,
      dfvs: Opt[Dict[AnNameT, DfvPairL]] = None,
      depth: int = 0, # useful when using widening
  ):
    self.dfvs = dfvs if dfvs else {}
    self.depth = depth


  def setIncDepth(self, other: 'AnDfvPairDict'):
    """Set depth one more that the other's depth (prev value's depth)."""
    self.depth = other.depth + 1


  def decDepth(self) -> int:
    """Decrement depth by 1."""
    self.depth -= 1
    return self.depth


  def setValue(self,
      anName: AnNameT,
      nDfv: DfvPairL,
  ) -> None:
    self.dfvs[anName] = nDfv


  def getCopy(self, deep: bool = True):
    if deep:
      return AnDfvPairDict({k: v.getCopy() for k, v in self.dfvs.items()}, self.depth)
    else:
      return AnDfvPairDict(self.dfvs.copy(), self.depth)


  def swapBiInOut(self) -> 'AnDfvPairDict':
    """Swaps IN and OUT. Returns a copy.
    This is useful in cases like the OUT of the end node in
    the global function is the IN of the main() function,
    and the IN of global function is useful in the OUT of main()
    function in case of backward analyses.
    """
    newBi = AnDfvPairDict(None, depth=self.depth)
    for anName, nDfv in self.dfvs.items():
      newBi[anName] = DfvPairL(nDfv.dfvOut, nDfv.dfvIn)
    return newBi


  def __contains__(self, anName: AnNameT):
    return anName in self.dfvs


  def __iter__(self):
    return iter(self.dfvs.items())


  def __getitem__(self, anName: AnNameT):
    return self.dfvs[anName]


  def __setitem__(self, key: AnNameT, val: DfvPairL):
    self.dfvs[key] = val


  def __eq__(self, other):
    if self is other: return True
    equal = True
    if not isinstance(other, AnDfvPairDict):
      equal = False
    elif not self.depth == other.depth:
      equal = False
    elif not self.dfvs.keys() == other.dfvs.keys():
      equal = False
    else:
      for anName, nDfvSelf in self.dfvs.items():
        if anName not in other:
          equal = False
          break
        nDfvOther = other[anName]
        direction = clients.getAnDirn(anName)
        if direction == Forward:
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
    idStr = "" if not util.DD5 else f"(id:{id(self)})"
    sio = io.StringIO()
    sio.write(f"DfvDict(Depth:{self.depth}){idStr}:")
    for anName in sorted(self.dfvs.keys()):
      sio.write(f"\n{anName}:\n{self.dfvs[anName]}")
    return sio.getvalue()


  def __repr__(self): return self.__str__()





