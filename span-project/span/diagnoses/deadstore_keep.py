#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""The dead code diagnosis reporter.

Although this module is not used currently,
keep it for reference on how to use the clang's
bug reporting system.
"""

import logging

LOG = logging.getLogger(__name__)

from typing import List, Optional as Opt, Dict, Set, cast
import io

import span.api.analysis as analysis
import span.api.dfv as dfv
import span.api.diagnosis as diagnosis

import span.ir.types as types
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.tunit as irTUnit
import span.ir.constructs as obj
import span.ir.ir as ir

from span.api.diagnosis import ClangReport, ClangMessage

# import the analysis classes
from span.clients.stronglive import StrongLiveVarsA
from span.clients.pointsto import PointsToA
import span.clients.pointsto as pointsto
import span.clients.stronglive as liveness
import span.clients as clients


class DeadStoreR(diagnosis.DiagnosisRT):
  """Reports the dead stores (assignments) found."""
  Needs = [StrongLiveVarsA]
  OptionalNeeds = [PointsToA]
  # AnalysesSeqCascading = [["StrongLiveVarsA"], ["PointsToA"], ["StrongLiveVarsA"], ["PointsToA"]]
  # AnalysesSeqLerner = [["StrongLiveVarsA", "PointsToA"]]
  AnalysesSeqCascading = [["ConstA"], ["PointsToA"],
                          ["ConstA"], ["PointsToA"], ["StrongLiveVarsA"]]
  AnalysesSeqLerner = [["ConstA", "PointsToA", "StrongLiveVarsA"]]


  def __init__(self):
    self.name = "Dead Code"
    self.category = "Dead Store"


  def handleResults(self,
      results: Opt[Dict[analysis.AnalysisNameT,
                             Dict[types.NodeIdT, dfv.DfvPairL]]],
      func: obj.Func,
  ) -> Opt[List[ClangReport]]:
    reports: List[ClangReport] = []

    assert results, f"{func}: {results}"
    liveVars = results[StrongLiveVarsA.__name__]
    pointsTo = results[PointsToA.__name__]

    assert func.cfg, f"{func}"
    for nodeId, node in func.cfg.nodeMap.items():
      insn = node.insn
      message = ""

      pointsToDfvIn = pointsTo[nodeId].dfvIn
      if pointsToDfvIn.top:
        assert not pointsToDfvIn.val
        message = f"Unreachable code"

      elif isinstance(insn, instr.AssignI):
        lhs = insn.lhs
        liveOut = cast(liveness.OverallL, liveVars[nodeId].dfvOut)

        if isinstance(lhs, expr.VarE):
          varName = lhs.name
          if (not liveOut.bot) and \
              (liveOut.top or (liveOut.val and varName not in liveOut.val)):
            if ir.isTmpVar(varName):
              message = f"Value of the above expression is unused"
            else:
              message = f"This value of {lhs} is unused"

        elif isinstance(lhs, expr.DerefE):
          print("SPAN UnaryE lhs:", insn, liveOut.val)

          assert isinstance(lhs.arg, expr.VarE), f"{insn}"
          lhsPtr: expr.VarE = lhs.arg
          # taking in value, since pointer may not be live at out
          # hence its information may have been purged
          ptrIn = cast(pointsto.OverallL, pointsTo[nodeId].dfvIn)
          print(ptrIn.val)

          if ptrIn.bot and liveOut.bot:
            message = f"None of the destinations are used ahead"
          else:
            pointees = ptrIn.getVal(lhsPtr.name)
            print("pointees: ", pointees)
            usedVars = liveVars[nodeId].dfvOut.val
            if not usedVars or (pointees and not (pointees & usedVars)):
              message = f"None of the destinations are used ahead"

      assert insn.info, f"{insn}"
      if message and insn.info.loc:
        report = ClangReport(self.name, self.category)
        messageObj = ClangMessage(msg=message, loc=insn.info.loc)
        report.addMessage(messageObj)
        reports.append(report)

    return reports
