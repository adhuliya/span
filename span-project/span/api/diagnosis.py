#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Program diagnosis tools and interface."""

import logging
LOG = logging.getLogger(__name__)
LDB = LOG.debug

from span.ir.tunit import TranslationUnit
from span.sys.ipa import IpaHost, ipaAnalyzeCascade


from typing import List, Optional as Opt, Dict, Type, Set, Any, TypeVar
import io

import span.util.util as util
from span.api.dfv import AnResult # replacing span.sys.common.AnResult

from span.api.analysis import (AnalysisNameT, AnalysisAT, AnalysisAT_T, )
from span.api.dfv import (DfvPairL,)
from span.ir.types import (Loc, NodeIdT, FuncNameT, AnNameT, )

from span.ir.constructs import Func

DiagnosisNameT = str

MethodT = str
PlainMethod: MethodT = "plain"
"""Run analyses using a 'Plain' Method (whatever the user intends)."""
CascadingMethod: MethodT = "cascading"
"""Run analyses using Cascading Method."""
LernerMethod: MethodT = "lerner"
"""Run analyses using Lerner's Method."""
SpanMethod: MethodT = "span"
"""Run analyses using Span Method."""
CompareAll: MethodT = "compareall"
"""Special method to denote a comparison of results of all the given methods."""
UseAllMethods: MethodT = "all"
"""A special method to invoke all given methods."""

AllMethods: Set[MethodT] = {
  PlainMethod,
  CascadingMethod,
  LernerMethod,
  SpanMethod,
  CompareAll,
  UseAllMethods,
}

class ClangMessage:
  """A message and location of the diagnostic report."""


  def __init__(self,
      msg: str,
      loc: Loc,
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


class ClangReport:
  """A diagnosis report with many message(s)."""


  def __init__(self,
      name: str,
      category: str,
      messages: Opt[List[ClangMessage]] = None,  # first msg is the master
  ) -> None:
    self.name = name
    self.category = category
    self.messages = messages


  def addMessage(self,
      message: ClangMessage,
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


class MethodDetail:
  """Method details on how to compute results.

  This class just holds the "name" of the method,
  and the analyses that it may need to compute DFVs.
  Based on this class object, appropriate logic is
  invoked by the user.
  """
  def __init__(self,
      name: str,
      anNames: List, # list of analyses the method uses
      subName: str = "",
      description: str = "No Description",
  ):
    self.name = name
    self.anNames = anNames
    self.subName = subName if subName else name
    self.description = description


  def __str__(self):
    return f"MethodDetail({self.name}, {self.subName}," \
           f" {self.anNames}, {repr(self.description)})"


  def __repr__(self):
    return str(self)


class DiagnosisRT:
  """The base class for all diagnoses.

  To define and run a custom diagnosis, create a child class,
  in a module in `span.diagnoses` package.
  """

  #NOTE: A default init for reference only. Must Override.
  MethodSequence: List[MethodDetail] = [
    MethodDetail(
      name=PlainMethod,
      anNames=["IntervalA"],
    ),
    MethodDetail(
      name=CascadingMethod,
      anNames=["IntervalA", "PointsToA"],
    ),
    MethodDetail(
      name=LernerMethod,
      anNames=["IntervalA", "PointsToA"],
    ),
    MethodDetail(
      name=SpanMethod,
      anNames=["IntervalA", "PointsToA"],
    ),
  ]
  """Holds a sequence of `MethodDetail`.
  
  See `span.sys.diagnosis` module on how this list is used.
  """


  def __init__(self, name: str, category: str, tUnit: TranslationUnit):
    self.name = name
    self.category = category
    self.tUnit = tUnit


  def init(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> None:
    """Override this method to do some initialization."""
    print("-" * 48) # a pretty printing


  def computeDfvs(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Opt[Dict[FuncNameT, Dict[AnNameT, AnResult]]]:
    """Compute the DFVs of various analysis using a desired method.

    Override this function to run any desired method with a desired subName.
    This is a default implementation. Please Override if needed.
    """
    if util.LL0: LDB("ComputeDFVs: Method=%s", method)

    res = None
    if method.name == PlainMethod:
      res = self.computeDfvsUsingPlainMethod(method, anClassMap)
    elif method.name == CascadingMethod:
      res = self.computeDfvsUsingCascadingMethod(method, anClassMap)
    elif method.name == LernerMethod:
      res = self.computeDfvsUsingLernerMethod(method, anClassMap)
    elif method.name == SpanMethod:
      res = self.computeDfvsUsingSpanMethod(method, anClassMap)
    elif method.name == CompareAll:
      res = self.compareAll(method, anClassMap)

    return res


  def computeResults(self,
      method: MethodDetail,
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> Any:
    """Compute the desired result using the computed DFVs of analyses,
    in `DiagnosisRT.computeDfvs` method."""
    raise NotImplementedError()


  def handleResults(self,
      method: MethodDetail,
      result: Any, # Any type that a particular implementation needs.
      dfvs: Dict[FuncNameT, Dict[AnNameT, AnResult]],
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> None:
    """Process the results computed by `DiagnosisRT.computeResults`.

    Operations like dumping the results to a file or printing it,
    can be done here.

    Analyze the analysis results and produce reports.

    Args:
      result: A custom object of results.
      dfvs: The DFVs that were computed by running analyses.
      anClassMap: Analyses names mapped to their classes.

    Returns:
      Nothing.
    """
    raise NotImplementedError()


  def finish(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT]],
  ) -> None:
    """Override this method to do some work after all operations finish."""
    print("-" * 48) # a pretty printing


  def computeDfvsUsingPlainMethod(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> Opt[Dict[FuncNameT, Dict[AnNameT, AnResult]]]:
    """A default implementation. Please Override."""
    assert len(anClassMap) == 1, f"{anClassMap}"

    mainAnalysis = method.anNames[0]
    ipaHost = IpaHost(
      self.tUnit,
      mainAnName=mainAnalysis,
      maxNumOfAnalyses=1,
    )
    res = ipaHost.analyze()

    return res


  def computeDfvsUsingSpanMethod(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
    """A default implementation. Please Override."""
    assert len(anClassMap) == 2, f"{anClassMap}"

    mainAnalysis = method.anNames[0]
    ipaHost = IpaHost(
      self.tUnit,
      mainAnName=mainAnalysis,
      otherAnalyses=method.anNames[1:],
      maxNumOfAnalyses=len(method.anNames),
    )
    res = ipaHost.analyze()

    return res


  def computeDfvsUsingLernerMethod(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
    """A default implementation. Please Override."""
    assert len(anClassMap) == 2, f"{anClassMap}"

    mainAnalysis = method.anNames[0]
    ipaHost = IpaHost(
      self.tUnit,
      mainAnName=mainAnalysis,
      otherAnalyses=method.anNames[1:],
      maxNumOfAnalyses=len(method.anNames),
      useTransformation=True, # this induces lerner's method
    )
    res = ipaHost.analyze()

    return res


  def computeDfvsUsingCascadingMethod(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> Dict[FuncNameT, Dict[AnNameT, AnResult]]:
    """A default implementation. Please Override."""
    assert len(anClassMap) == 2, f"{anClassMap}"

    res = ipaAnalyzeCascade(self.tUnit, method.anNames)
    return res


  def compareAll(self,
      method: MethodDetail,
      anClassMap: Dict[AnNameT, Type[AnalysisAT_T]],
  ) -> None:
    """Compares the results already computed using other methods."""
    pass


DiagnosisRClassT = TypeVar('DiagnosisRClassT', bound=DiagnosisRT)


def dumpClangReports(sourceFileName: str,  # e.g. "hello.c"
    reports: Opt[List[ClangReport]],
) -> None:
  """Write Clang reports to a `.clangreport` file.

  E.g. for `hello.c`, `hello.c.clangreport` is generated.
  It creates an empty file if there are no reports given.
  """
  destFileName = sourceFileName + ".clangreport"

  if not reports:
    util.writeToFile(destFileName, "")
    return

  with io.StringIO() as sio:
    for report in reports:
      sio.write(str(report))
      sio.write("\n")
    content = sio.getvalue()

  util.writeToFile(destFileName, content)
