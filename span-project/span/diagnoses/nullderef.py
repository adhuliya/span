#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""The dead code diagnosis reporter."""

import logging

LOG = logging.getLogger("span")

from typing import List, Optional as Opt, Dict, Set, cast
import io

import span.api.analysis as analysis
import span.api.dfv as dfv
import span.api.diagnosis as diagnosis

import span.ir.types as types
import span.ir.conv as irConv
import span.ir.op as op
import span.ir.expr as expr
import span.ir.instr as instr
import span.ir.tunit as irTUnit
import span.ir.constructs as obj
import span.ir.ir as ir

from span.util.util import LS
from span.api.diagnosis import Report, Message

# import the analysis classes
from span.clients.pointsto import PointsToA
import span.clients.pointsto as pointsto


class NullDerefR(diagnosis.DiagnosisRT):
  """Reports the possible NULL dereferences."""
  Needs = [PointsToA]
  OptionalNeeds: List[type] = []
  # AnalysesSeqCascading = [["ConstA"], ["PointsToA"], ["EvenOddA"]]
  # AnalysesSeqLerner = [["LiveVarsA", "PointsToA"]]
  AnalysesSeqCascading = [["ConstA"], ["PointsToA"],
                          ["ConstA"], ["EvenOddA"], ["PointsToA"]]
  AnalysesSeqLerner = [["ConstA", "PointsToA", "EvenOddA"]]


  # AnalysesSeqLerner = [["ConstA", "PointsToA"]]
  # AnalysesSeqLerner = [["PointsToA"]]

  def __init__(self):
    self.name = "Null Deref"
    self.category = "SPAN Ptr"


  def handleResults(self,
      results: Dict[analysis.AnalysisNameT,
                           Dict[types.Nid, dfv.NodeDfvL]],
      func: obj.Func,
  ) -> Opt[List[Report]]:
    reports: List[Report] = []
    if func.sig.variadic:  # SkipVariadicFunctions
      if LS: LOG.info("SkippingVariadicFunction: %s", func.name)
      return reports

    pointsTo = results[PointsToA.__name__]

    assert func.cfg, f"{func}"
    for nodeId, node in func.cfg.nodeMap.items():
      insn = node.insn
      message = ""
      derefObjLoc = None

      pointsToDfvIn = cast(pointsto.OverallL, pointsTo[nodeId].dfvIn)
      if isinstance(insn, instr.AssignI):
        lhs = insn.lhs
        rhs = insn.rhs

        derefvarName = ""
        derefObjLoc = None
        litNames = None

        # if there is a dereference happening,
        # fetch the name of the variable dereferenced.
        if lhs.hasDereference() and not isinstance(rhs, expr.AddrOfE):
          if isinstance(lhs, expr.ArrayE):
            litNames = {lhs.of.name}
          else:
            litNames = ir.getNamesUsedInExprSyntactically(lhs)
          assert lhs.info, f"{nodeId}: {insn}"
          derefObjLoc = lhs.info.loc
        elif rhs.hasDereference() and not isinstance(rhs, expr.AddrOfE):
          if isinstance(rhs, expr.ArrayE):
            litNames = {rhs.of.name}
          else:
            litNames = ir.getNamesUsedInExprSyntactically(rhs)
          assert rhs.info, f"{nodeId}: {insn}"
          derefObjLoc = rhs.info.loc

        if not litNames:
          continue  # there is no dereference

        assert len(litNames) == 1, f"{lhs}: {litNames}"  # sanity check
        for name in litNames:  # loop runs only once
          derefvarName = name

        # get dfv of the pointer
        ptrVal = cast(pointsto.ComponentL, pointsToDfvIn.getVal(derefvarName))

        if LS and derefvarName == "v:spec_random_load:8t":
          LOG.info(f"ptrdfvInOf {node} = {ptrVal}")

        if ptrVal.top:
          pass  # nothing
        elif ptrVal.bot:
          message = f"{derefvarName} may be NULL (a minor possibility)"
        else:
          assert ptrVal.val
          if irConv.NULL_OBJ_NAME in ptrVal.val and len(ptrVal.val) == 1:
            message = f"{derefvarName} is NULL"
          elif irConv.NULL_OBJ_NAME in ptrVal.val:
            message = f"{derefvarName} may be NULL"

      if message and derefObjLoc:
        report = Report(self.name, self.category)
        messageObj = Message(msg=message, loc=derefObjLoc)
        report.addMessage(messageObj)
        reports.append(report)

    return reports
