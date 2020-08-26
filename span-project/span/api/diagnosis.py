#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Program diagnosis tools and interface."""

import logging

LOG = logging.getLogger("span")

from typing import List, Optional as Opt, Dict
import io

import span.util.util as util

import span.api.analysis as analysis
import span.api.dfv as dfv
import span.ir.types as types
import span.ir.constructs as obj

AnalysisClassT = type
DiagnosisNameT = str
DiagnosisClassT = type


class Message:
  """A message and location of the diagnostic report."""


  def __init__(self,
      msg: str,
      loc: types.Loc,
  ) -> None:
    self.msg = msg
    self.loc = loc


  def __str__(self) -> str:
    with io.StringIO() as sio:
      sio.write(f"LINE {self.loc.line}\n")
      sio.write(f"COLUMN {self.loc.col}\n")
      sio.write(f"MESSAGE {self.msg}\n")
      ret = sio.getvalue()
    return ret


class Report:
  """A diagnosis report with many message(s)."""


  def __init__(self,
      name: str,
      category: str,
      messages: Opt[List[Message]] = None,  # first msg is the master
  ) -> None:
    self.name = name
    self.category = category
    self.messages = messages


  def addMessage(self,
      message: Message,
  ) -> None:
    self.messages = self.messages if self.messages else []
    self.messages.append(message)


  def __str__(self) -> str:
    with io.StringIO() as sio:
      sio.write("START\n")
      sio.write(f"NAME {self.name}\n")
      sio.write(f"CATEGORY {self.category}\n")

      if self.messages:
        for message in self.messages:
          sio.write(f"{message}")

      sio.write("END\n")
      ret = sio.getvalue()
    return ret


class DiagnosisRT(types.AnyT):
  """The base class for all diagnoses reporting classes.
  Changed suffix "DT" to "RT" since "D" was clashing with Direction (ForwardD..)
  """
  # the list of analyses, needed by the diagnostic class
  Needs: List[AnalysisClassT] = []

  # the list of analyses, optionally needed by the diagnostic class
  # i.e. if this optional requirement is not met,
  # diagnosis just becomes less precise
  OptionalNeeds: List[AnalysisClassT] = []

  AnalysesSeqCascading: Opt[List[List[analysis.AnalysisNameT]]] = None
  AnalysesSeqLerner: Opt[List[List[analysis.AnalysisNameT]]] = None


  def __init__(self):
    super().__init__()


  def handleResults(self,
      results: Dict[analysis.AnalysisNameT,
                          Dict[types.NodeIdT, dfv.NodeDfvL]],
      func: obj.Func,
  ) -> Opt[List[Report]]:
    """
    Analyze the analysis results and produce reports.

    Args:
      results: dictionary of analysis results for each analysis.
               The analyses in the dict are the ones requested in,
               Needs and OptionalNeeds class member variables.
      func: the obj.Func object the diagnosis is to run on

    Returns:
      List of reports that are to be delivered to Clang.
    """
    raise NotImplementedError()


def dumpReports(sourceFileName: str,  # e.g. "hello.c"
    reports: Opt[List[Report]],
) -> None:
  """Write reports to a `.spanreport` file.

  E.g. for `hello.c`, `hello.c.spanreport` is generated.
  It creates an empty file if there are no reports given.
  """
  destFileName = sourceFileName + ".spanreport"

  if not reports:
    util.writeToFile(destFileName, "")
    return

  with io.StringIO() as sio:
    for report in reports:
      sio.write(str(report))
      sio.write("\n")
    content = sio.getvalue()

  util.writeToFile(destFileName, content)
