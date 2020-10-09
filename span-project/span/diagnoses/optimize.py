#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Optimize the C program."""

import logging

from span.ir.constructs import Func

LOG = logging.getLogger("span")
from typing import Optional as Opt, Dict


from span.ir.tunit import TranslationUnit
from span.sys.host import Host
from span.sys.ipa import IpaHost


class TransformInfo:
  """This class represents the transformation information."""
  def __init__(self, value):
    self.value = value
    self.loc = None
    self.tType = None # transformation type


class TransformCode:
  def __init__(self,
      tUnit: TranslationUnit,
      ipaEnabled: bool = True
  ):
    self.tUnit = tUnit
    self.ipaEnabled = ipaEnabled
    self.analyses = ["IntervalA", "PointsToA"]
    self.ipaHost: Opt[IpaHost] = None
    self.intraHosts: Opt[Dict[Func, Host]] = None


  def main(self):
    self.analyze()
    self.genTransformInfoAll()
    self.dumpTransformInfo()


  def analyze(self):
    """Analyze the C program."""
    mainAnalysis = self.analyses[0]
    otherAnalyses = self.analyses[1:]
    maxNumOfAnalyses = len(self.analyses)

    ipaHostSpan = IpaHost(self.tUnit,
                          mainAnName=mainAnalysis,
                          otherAnalyses=otherAnalyses,
                          maxNumOfAnalyses=maxNumOfAnalyses
                          )
    ipaHostSpan.analyze()
    self.ipaHost = ipaHostSpan


  def genTransformInfoAll(self) -> None:
    """Generate the whole transformation information."""
    assert self.ipaHost or self.intraHosts, f"No analysis results"
    if self.ipaEnabled:
      assert self.ipaHost, f"No analysis results"
    else:
      assert self.intraHosts, f"No analysis results"

    host = self.ipaHost if self.ipaEnabled else self.intraHosts
    for func in self.tUnit.yieldFunctionsForAnalysis():
      funcResults = host.finalResult[func.name]
      self.genTransformInfoFunc(func, funcResults)


  def genTransformInfoFunc(self, func: Func, funcResults: Dict) -> None:
    """Generate the transformation information for a function."""
    pass


  def dumpTransformInfo(self):
    """Output the transform info to a file."""
    pass


