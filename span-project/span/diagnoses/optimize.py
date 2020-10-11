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


class TrInfo: # TransformationInfo
  """This class represents the transformation information."""
  def __init__(self, value):
    self.trType = None # transformation type
    self.loc = None
    self.value = value


  def __str__(self):
    return f"TrInfo({self.trType}, {self.value}, {self.loc})"


  def __repr__(self):
    return self.__str__()


class TransformCode:
  """This class analyzes the TranslationUnit and transforms it
  to optimize"""
  def __init__(self,
      tUnit: TranslationUnit,
      ipaEnabled: bool = True
  ):
    self.tUnit = tUnit
    self.ipaEnabled = ipaEnabled
    self.analyses = ["IntervalA", "PointsToA"]
    self.ipaHost: Opt[IpaHost] = None
    self.intraHosts: Opt[Dict[Func, Host]] = None


  # mainentry
  def transform(self):
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
    intervalRes = funcResults["IntervalA"]
    for node in func.cfg.yieldNodes():
      nid, insn = node.id, node.insn
      pass #TODO



  def dumpTransformInfo(self):
    """Output the transform info to a file."""
    pass


