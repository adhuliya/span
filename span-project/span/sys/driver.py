#!/usr/bin/env python3.6

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Python 3.6 or above.

This is the driver module that invokes the SPAN.
This module is supposed to be used by the 'main' module
which is exposed as command `span`.
"""
import span.util.logger as logger
import logging
# Initialize -- logger, etc.
# @PRODUCTION: use span.util.util.LL<0-5> to control logging.
logger.initLogger(appName="span", logLevel=logger.LogLevels.DEBUG)

LOG: logging.Logger = logging.getLogger("span")

import span.ir.callgraph
import io
import os
import os.path as osp
import time
import sys
import subprocess as subp
import re
import argparse
from typing import List, Tuple, Dict
from typing import Optional as Opt
import span.ir.types as types
import span.ir.conv as irConv
import span.sys.ddm as ddm
import span.util.consts as consts

import span.ir.tunit      as tunit
import span.ir.ir         as ir
import span.ir.util       as irUtil
import span.api.analysis  as an
import span.ir.ipa        as irIpa
import span.ir.query      as irQuery

import span.util.util     as util
import span.util.ff       as ff

import span.sys.host      as host
import span.sys.ipa       as sysIpa
import span.sys.clients   as clients
import span.sys.diagnosis as sysDiagnosis
import span.api.diagnosis as apiDiagnosis
import span.sys.optimize  as sysOpt
sysDiagnosis.init()  # IMPORTANT

installDotMsg = """
SPAN: `xdot` error: cannot locate program to view graphviz dot files.
If on Ubuntu, try installing xdot with,
  sudo apt-get update
  sudo apt-get install xdot
"""

SLICE_POINT_REGEX = r"(\d+)([iI][nN]|[oO][uU][tT])?"
"""
The slice points like: 8in, 8out denote IN of 8 and OUT of 8.
Just a number 8 is same as 8in.
"""

AN_NAME_REGEX = r"[+-]\w+"
"""A regex for analysis names (always prefixed with +/-)."""

SPAN_AN_SPEC_REGEX = (r"(?P<slash>/?)(?P<analyses>([+]\w+)([~+-]\w+)*)"
                      r"(?P=slash)")
"""Regex to specify list of analyses. Some examples are,

    +Analysis1+Analysis2
    
This tells the system to run both the analyses,
and add any other analysis if needed.

    +Analysis1-Analysis2
    
This tells the system to run Analysis1 but never use Analysis2,
and add any other analysis if needed.

    /+Analysis1+Analysis2/
    
This tells the system to run both the analyses,
and **not** add any other analysis **even if needed**.
"""

CASC_AN_SPEC_REGEX = r"(?P<analyses>/([+]\w+)+/)+"
"""Analysis spec regex for cascading/lerner."""

C_FILENAME_REGEX = re.compile(r"^.*\.c")
"""A C file should always have a `.c` suffix."""

SPANIR_FILENAME_REGEX = re.compile(r"^.*\.c.spanir")
"""A C file's SPAN IR file should always have a `.c.spanir` suffix."""

cOrSpanirFile = "The .c or .spanir file."


def getRegisteredAnalyses() -> str:
  """Returns the name and description of registered analysis."""
  sio = io.StringIO()
  for anName, anClass in clients.analyses.items():
    doc = anClass.__doc__ if anClass.__doc__ else "No Description"
    doc = doc[:50]
    if len(doc) == 50: doc += "..."
    sio.write(f"'{anName}': {doc}, ")

  return sio.getvalue()

analysisSpecString = f"Specification of analyses" \
                     f" to run choose from {getRegisteredAnalyses()}"


def getRegisteredAnalysesList() -> List[str]:
  """Returns the list of registered analysis names."""
  return list(clients.analyses.keys())


def getRegisteredAnalyses() -> str:
  """Returns the name and description of registered analysis."""
  sio = io.StringIO()
  for anName, anClass in clients.analyses.items():
    doc = anClass.__doc__ if anClass.__doc__ else "No Description"
    doc = doc[:50]
    if len(doc) == 50: doc += "..."
    sio.write(f"'{anName}': {doc}, ")

  return sio.getvalue()


def getRegisteredDiagnosesList() -> List[str]:
  """Returns the list of registered diagnoses names."""
  return list(sysDiagnosis.allDiagnoses.keys())


def getRegisteredDiagnoses() -> str:
  """Returns the name and description of registered diagnoses."""
  sio = io.StringIO()
  for diName, diClass in sysDiagnosis.allDiagnoses.items():
    doc = diClass.__doc__ if diClass.__doc__ else "No Description"
    doc = doc[:50]
    if len(doc) == 50: doc += "..."
    sio.write(f"'{diName}': {doc}, ")

  return sio.getvalue()


def c2spanirArgParse(args: argparse.Namespace) -> int:
  """Processes cmd line args and invokes `c2spanir()`."""
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupCC(args.check)
  util.setupDD(args.detail)
  return c2spanir(args.fileName)


def c2spanir(cFileName: str = None) -> int:
  """
  Converts the C file to SPAN IR
  e.g. takes hello.c and produces hello.c.spanir
  """
  if not cFileName:
    cFileName = sys.argv[2]

  util.exitIfProgramDoesnotExist("clang")

  cmd = f"clang --analyze -Xanalyzer -analyzer-checker=core.span.SlangGenAst" \
        f" {cFileName} 2> {cFileName}.clang.log"

  if util.VV1: print("running> ", cmd)
  completed = subp.run(cmd, shell=True)
  if util.VV1: print("SPAN: clang return code:", completed.returncode)
  if completed.returncode != 0:
    print("SPAN: ERROR.")
    print("Maybe an invalid C program!")
    print("Try compiling the input program first, to check its validity.")
    return completed.returncode
  return 0


def ipaDiagnoseSpanIr(args: argparse.Namespace) -> None:
  diName    = args.diagnosisName
  fileName = args.fileName
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  spanirFileName = convertIfCFile(fileName)
  if util.VV1: print("Filename:", fileName, spanirFileName)
  currTUnit = parseTUnitObject(spanirFileName, ipa=True)

  if diName == "interval":
    sysIpa.diagnoseInterval(currTUnit)
  else:
    raise ValueError(f"Unknown diagnosis name: {diName}")


def optimizeSpanIr(args: argparse.Namespace) -> None:
  optName = args.optName
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  currTUnit = parseTUnitObject(args.fileName, ipa=True)

  if optName == "all":
    trCodeObj = sysOpt.TransformCode(currTUnit, ipaEnabled=True)
    trCodeObj.transform()

def diagnoseSpanIr(args: argparse.Namespace) -> None:
  """Runs the given diagnosis on the spanir file for each function."""
  diName = args.diagnosisName
  cascade = args.diagnosisStyle == "cascade"
  lerner  = args.diagnosisStyle == "lerner"
  span    = args.diagnosisStyle == "span" # default case too
  fileName = args.fileName
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  spanirFileName = convertIfCFile(fileName)
  currTUnit: tunit.TranslationUnit = ir.readSpanIr(spanirFileName)

  reports = []
  for func in currTUnit.yieldFunctionsWithBody():
    if func.basicBlocks: # if function is not empty
      report = sysDiagnosis.runDiagnosis(diName, func,
                                         cascade=cascade, lerner=lerner)
      if report:
        reports.extend(report)

  # sort the reports
  reports.sort(key=lambda r:
  (r.messages[0].loc.line, r.messages[0].loc.col))  # type: ignore
  # dump the span reports in the designated file
  apiDiagnosis.dumpReports(currTUnit.name, reports)

  # now run scan-build to visualize the reports
  # if not reports:
  #   print("No report generated.")
  #   exit(0)
  # return # to avoid the diagnosis reports to display (delit - its temporary)

  util.exitIfProgramDoesnotExist("clang")
  util.exitIfProgramDoesnotExist("scan-build")

  includesString = getIncludesString()
  cFileName = ".".join(spanirFileName.split(".")[:-1]) # remove .spanir extension
  cmd = consts.CMD_F_SLANG_BUG.format(includesString=includesString, cFileName=cFileName)
  completed = subp.run(cmd, shell=True)
  if util.VV1: print("Return Code:", completed.returncode)
  if completed.returncode != 0:
    print("SPAN: ERROR.")


def getIncludesString() -> str:
  """Gets C header files dir includes string from a file `includes.txt` in
  the current directory (if it exists)"""
  if not os.path.exists("includes.txt"):
    print("No includes.txt file present.")
    return ""

  with open("includes.txt") as f:
    includesString = f.read()

  includesString = includesString.strip()
  return includesString


def parseSpanAnalysisExpr(anNamesExpr: str) -> Tuple[str, list, list, list, int]:
  """Parse the analysis expression as specified by
  `SPAN_AN_SPEC_REGEX` (for span) and return the result."""
  mainAnalysis      = ""
  otherAnalyses     = []
  supportAnalyses   = []
  avoidAnalyses     = []

  pat = re.compile(SPAN_AN_SPEC_REGEX)

  m = pat.match(anNamesExpr)
  assert m, f"{anNamesExpr}"

  maxAnalysisCount = 0 if m.group("slash") else 1024 # a large number
  analysisCount = 0

  anNames = re.findall(r"[~+-]\w+", anNamesExpr)

  for anName in anNames:
    prefix = anName[0]
    onlyAnName = anName[1:]
    if onlyAnName not in clients.analyses:
      raise ValueError(f"{consts.AN_NOT_PRESENT}: {onlyAnName}")

    if prefix == "+":
      analysisCount += 1
      if not mainAnalysis:
        mainAnalysis = onlyAnName
      else:
        otherAnalyses.append(onlyAnName)
    elif prefix == "-":
      avoidAnalyses.append(onlyAnName)
    elif prefix == "~":
      analysisCount += 1
      supportAnalyses.append(onlyAnName)
    else:
      raise ValueError(f"{consts.ILLFORMED_AN_EXPR}: f{anNamesExpr}")

  maxAnalysisCount = max(analysisCount, maxAnalysisCount)

  return mainAnalysis, otherAnalyses, supportAnalyses, avoidAnalyses, maxAnalysisCount


def parseCascadingAnalysisExpr(anNamesExpr: str) -> Tuple[str, list, list, int]:
  """Parse the analysis expression as specified by
  `SPAN_AN_SPEC_REGEX` (for cascading/lerner) and return the result."""
  mainAnalysis      = ""
  otherAnalyses     = []
  avoidAnalyses     = []
  maxAnalysisCount  = ff.MAX_ANALYSES # a large number

  if anNamesExpr[0] == "/" and anNamesExpr[-1] == "/":
    maxAnalysisCount = 0
    if anNamesExpr[0] == "/" and anNamesExpr[-1] != "/" or \
        anNamesExpr[0] != "/" and anNamesExpr[-1] == "/":
      exit(20)
    anNamesExpr = anNamesExpr[1:-1]

  givenAnalyses = re.findall(r"[+-]\w+", anNamesExpr)

  for anName in givenAnalyses:
    prefix = anName[0]
    onlyAnName = anName[1:]
    if onlyAnName not in clients.analyses:
      raise ValueError(f"{consts.AN_NOT_PRESENT}: {onlyAnName}")
    if prefix == "+":
      maxAnalysisCount += 1
      if not mainAnalysis:
        mainAnalysis = onlyAnName
      else:
        otherAnalyses.append(onlyAnName)
    elif anName[0] == "-":
      avoidAnalyses.append(onlyAnName)
    else:
      raise ValueError(f"{consts.ILLFORMED_AN_EXPR}: f{anNamesExpr}")

  return mainAnalysis, otherAnalyses, avoidAnalyses, maxAnalysisCount


def analyzeSpanIrIpa(args: argparse.Namespace) -> sysIpa.IpaHost:
  """Runs the given analyses on the whole spanir translation unit."""
  disableAllSim = True if args.subcommand == "ipa" else False
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  mainAnalysis, otherAnalyses, supportAnalyses, avoidAnalyses, maxAnalysisCount = \
    parseSpanAnalysisExpr(args.analyses)

  currTUnit = parseTUnitObject(args.fileName, True)

  ipa1 = sysIpa.IpaHost(
    tUnit           = currTUnit,
    mainAnName      = mainAnalysis,
    otherAnalyses   = otherAnalyses,
    supportAnalyses = supportAnalyses,
    avoidAnalyses   = avoidAnalyses,
    maxNumOfAnalyses= maxAnalysisCount,
    disableAllSim   = disableAllSim,
  )

  timer = util.Timer("IpaAnalysis")
  ipa1.analyze()
  timer.stopAndLog(util.VV1, util.LL1)
  return ipa1


def analyzeSpanIr(args: argparse.Namespace) -> Dict[types.FuncNameT, host.Host]:
  """Runs the given analyses on the spanir file for each function."""
  disableAllSim = True if args.subcommand == "analyze" else False
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)
  idemand = True if args.subcommand == "idemand" else False

  anNameExpr = args.analyses
  funcName = args.functionName

  funcName = None if not funcName else irConv.canonicalizeFuncName(funcName)

  mainAnalysis, otherAnalyses, supportAnalyses, avoidAnalyses, maxAnalysisCount = \
    parseSpanAnalysisExpr(anNameExpr)

  currTUnit = parseTUnitObject(args.fileName)

  if funcName is not None and funcName not in currTUnit.allFunctions:
    print(f"SPAN: ERROR: {funcName} not found.", file=sys.stderr)
    exit(42)

  if util.VV1: print("\nAnalyzing Function(s):", funcName if funcName else "ALL")
  timer = util.Timer("SpanAnalysis(with setups)")
  res, analysisTime = analyzeFunctions(currTUnit=currTUnit,
                                       funcName=funcName,
                                       mainAnName=mainAnalysis,
                                       otherAnalyses=otherAnalyses,
                                       supportAnalyses=supportAnalyses,
                                       avoidAnalyses=avoidAnalyses,
                                       maxNumOfAnalyses=maxAnalysisCount,
                                       disableAllSim=disableAllSim,
                                       useDdm=idemand)
  print()
  if util.VV1: print(f"TimeElapsed(SpanAnalysis(no   setups)): {analysisTime} ms")
  timer.stopAndLog(util.VV1, util.LL1)
  return res


def analyzeFunctions(
    currTUnit: tunit.TranslationUnit,
    funcName: Opt[types.FuncNameT],
    mainAnName: Opt[an.AnalysisNameT] = None,
    otherAnalyses: Opt[List[an.AnalysisNameT]] = None,
    supportAnalyses: Opt[List[an.AnalysisNameT]] = None,
    avoidAnalyses: Opt[List[an.AnalysisNameT]] = None,
    maxNumOfAnalyses: int = ff.MAX_ANALYSES,
    analysisSeq: Opt[List[List[an.AnalysisNameT]]] = None,  # for cascading/lerner
    disableAllSim: bool = False,
    useDdm: bool = False,
) -> Tuple[Dict[types.FuncNameT, host.Host], float]:
  """returns a tuple,
    * The Host object for each function (a dictionary)
    * total analysis time (only) in milliseconds
  """
  totalAnalysisTime: float = 0
  resultDict = {}

  for func in currTUnit.yieldFunctionsWithBody():
    if funcName and not funcName == func.name:
      continue
    if util.VV1: print("\n AnalyzingFunction(Intra):", func.name)
    syn1 = host.Host(
      func              = func,
      mainAnName        = mainAnName,
      otherAnalyses     = otherAnalyses,
      supportAnalyses   = supportAnalyses,
      avoidAnalyses     = avoidAnalyses,
      maxNumOfAnalyses  = maxNumOfAnalyses,
      # analysisSeq       = analysisSeq,
      disableSim        = disableAllSim,
      useDdm            = useDdm,
    )
    analysisTime = syn1.analyze() # do the analysis
    resultDict[func.name] = syn1 # save the host object
    totalAnalysisTime += analysisTime
    if util.VV2: print("HostObjectSize (after analysis):", util.getSize2(syn1))
    syn1.printOrLogResult() # print the result of each analysis

  return resultDict, totalAnalysisTime


def queryTranslationUnit(args: argparse.Namespace):
  """Query predefined information on the translation unit."""
  fileName = args.fileName
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)
  currTUnit = parseTUnitObject(fileName)

  irQuery.executeAllQueries(currTUnit)


def viewDotFile(args: argparse.Namespace):
  """Generates the dot files to view the IR better."""
  graphType = args.graphType
  fileName = args.fileName
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  funcName = args.functionName
  funcName = None if not funcName else irConv.canonicalizeFuncName(funcName)
  print("Showing Function(s):", funcName if funcName else "ALL")


  if graphType == "callgraph":
    currTUnit = parseTUnitObject(fileName)
    callGraph = span.ir.callgraph.generateCallGraph(currTUnit)
    callGraphDot = callGraph.getCallGraphDot()
    dotFileName = f"{fileName}.{graphType}.dot"
    util.writeToFile(dotFileName, callGraphDot)
    showDotGraph(dotFileName)
  else:
    currTUnit = parseTUnitObject(fileName, ipa=(graphType=="ipa-cfg"))

    for func in currTUnit.yieldFunctionsWithBody():
      if funcName and not func.name == funcName:
        continue
      if graphType in {"cfg", "ipa-cfg"}:
        callGraphDot = func.cfg.genBbDotGraph()
      elif graphType == "cfg_node":
        callGraphDot = func.cfg.genDotGraph()
      else:
        assert False

      dotFileName = f"{fileName}.{irConv.simplifyName(func.name)}.{graphType}.dot"
      util.writeToFile(dotFileName, callGraphDot)
      showDotGraph(dotFileName)


def showDotGraph(dotFileName: str) -> bool:
  """Invokes the `xdot` program to show the given dotfile."""
  if not util.programExists("xdot"):
    print(installDotMsg)
    return False
  else:
    util.exitIfProgramDoesnotExist("xdot")
    cmd = f"xdot {dotFileName} &"
    if util.VV1: print("running>", cmd)
    completed = subp.run(cmd, shell=True)
    if util.VV1: print("SPAN: xdot return Code:", completed.returncode)
    if completed.returncode != 0:
      print(installDotMsg)
      return False
  return True


def convertIfCFile(fileName: str) -> str:
  if C_FILENAME_REGEX.fullmatch(fileName):
    c2spanir(fileName)
    return f"{fileName}.spanir"
  return fileName


def testSpan(args: argparse.Namespace):
  """Invokes the unit and functional tests."""
  testType = args.testType
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  import span.tests.run as run
  run.runTests(testType)


def getCmdLineFuncName(funcName: Opt[types.FuncNameT]) -> Opt[types.FuncNameT]:
  return None if not funcName else irConv.canonicalizeFuncName(funcName)


def sliceDemand(args: argparse.Namespace):
  """Raises demand as provided in args."""
  ppPattern = re.compile(SLICE_POINT_REGEX)
  programPoint = args.programpoint
  vars = args.vars
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  funcName = getCmdLineFuncName(args.functionName)
  assert funcName, f"{args.functionName}"
  if util.VV1: print("Using Function(s):", funcName if funcName else "ALL")

  currTUnit = parseTUnitObject(args.fileName)
  func = currTUnit.getFuncObj(funcName)

  m = ppPattern.match(programPoint)
  assert m, f"{programPoint}"
  nid = int(m.group(1))
  assert func.cfg, f"{func}"
  node = func.cfg.nodeMap[nid]
  atIn = True if not m.group(2) else m.group(2).lower() == "in"
  varSet = frozenset(irConv.genLocalName(func.name, var) for var in vars.split(","))

  if util.VV1: print("Note: Assuming all nodes are feasible.")
  ddMethod = ddm.DdMethod(func)
  for varName in varSet:
    demand = ddm.AtomicDemand(func, node, atIn, varName,
                              ir.inferTypeOfVal(func, varName), irConv.Backward)
    if util.VV1: print("Got Slice:", ddMethod.propagateDemand(demand))
    if util.VV1: print("InfeasibleNodeDependence:", ddMethod.infNodeDep)


def simulateCascading(args: argparse.Namespace) -> Dict[types.FuncNameT, host.Host]:
  """Runs the cascaded analyses on the spanir file for each function."""
  anNameExpr = args.analyses
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  funcName = getCmdLineFuncName(args.functionName)
  if util.VV1: print("\n Analyzing Function(s):", funcName if funcName else "ALL")

  stepPattern = re.compile(r"/.*?/")
  allSteps = stepPattern.findall(anNameExpr)
  analysisSeq: List[List[an.AnalysisNameT]] = []

  for step in allSteps:
    mainAnalysis, otherAnalyses, _, _ = parseCascadingAnalysisExpr(step)
    analysisSeq.append([mainAnalysis])
    analysisSeq.append(otherAnalyses)

  currTUnit = parseTUnitObject(args.fileName)

  timer = util.Timer("CascadingAnalysis")
  res, _ = analyzeFunctions(currTUnit=currTUnit,
                            funcName=funcName,
                            analysisSeq=analysisSeq)
  timer.stopAndLog(util.VV1, util.LL1)
  return res


def dumpSpanIr(args: argparse.Namespace):
  """Dumps the pre-processed SPAN IR to the given file
  suffixed with `.spanir.processed` suffix.
  (used for testing purposes)
  Eg. for `test.c` or `test.c.spanir`, it generates
  `test.c.spanir.processed`
  """
  fileName = args.fileName
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  spanIrFileName = convertIfCFile(fileName)
  cFileName = extractCFileName(spanIrFileName)
  if not cFileName:
    exit(19)

  currTUnit: tunit.TranslationUnit = ir.readSpanIr(spanIrFileName)

  processedSpanIrString = repr(currTUnit)
  outFileName = f"{spanIrFileName}.processed"
  util.writeToFile(outFileName, processedSpanIrString)


def dumpSpanSettings(args: argparse.Namespace):
  """Dumps the current settings of SPAN."""
  util.setupLL(args.logging)
  util.setupVV(args.verbose)
  util.setupDD(args.detail)
  util.setupCC(args.check)

  import span.util.ff as ff

  print(ff.getModuleAttributesString())


def extractCFileName(fileName) -> Opt[str]:
  """Extracts the C source file name:
  It expects names to be starting with a C file name:
  test.c, test.c.spanir, etc."""
  baseName = os.path.basename(fileName)
  match = C_FILENAME_REGEX.search(baseName)
  if match:
    return match.group()
  return None


def parseTUnitObject(fileName: str, ipa=False) -> tunit.TranslationUnit:
  """Evals the spanir translation unit from the given file.
  If the input file is a C file (detected by its extension)
  it is first converted to spanir."""
  timer = util.Timer("ParseTranslationUnit")
  spanIrFileName  = convertIfCFile(fileName)
  cFileName       = extractCFileName(spanIrFileName)
  if not cFileName: exit(19)

  currTUnit: tunit.TranslationUnit = ir.readSpanIr(spanIrFileName)
  # if ipa: irIpa.preProcess(currTUnit)  # obsolete

  timer.stopAndLog(util.VV1, util.LL1)
  if util.VV1: print("TUnitObjSize:", util.getSize2(currTUnit))
  return currTUnit


# def handleSpanIrSerialization(args: argparse.Namespace):
#   """Handles converting SPAN IR to and from protobuf binary format"""
#   command = args.subcommand
#   fileName = args.fileName
#   newFileName = f"{extractCFileName(fileName)}.spanir.bin"
#
#   if command == "mem2bin":
#     currTUnit = parseTUnitObject(fileName)
#
#     protoSerializer = ir.ProtoSerializer(currTUnit)
#     protoSerializer.serializeTUnit(newFileName)
#
#   elif command == "bin2mem":
#     protoDeserializer = ir.ProtoDeserializer()
#     currTUnit = protoDeserializer.deserializeTUnit(newFileName)
#     print(currTUnit)


def slicePointRegex(argValue, pat=re.compile(SLICE_POINT_REGEX)):
  """Checks the slice point regex."""
  if not pat.match(argValue):
    raise argparse.ArgumentTypeError(f"expecting pattern {SLICE_POINT_REGEX}")
  return argValue


def spanAnSpecRegex(argValue, pat=re.compile(SPAN_AN_SPEC_REGEX)):
  """Checks the span analysis spec regex."""
  if not pat.match(argValue):
    raise argparse.ArgumentTypeError(f"expecting pattern {SPAN_AN_SPEC_REGEX}")
  return argValue


def cascAnSpecRegex(argValue, pat=re.compile(CASC_AN_SPEC_REGEX)):
  """Checks the cascading analysis spec regex."""
  if not pat.match(argValue):
    raise argparse.ArgumentTypeError(f"expecting pattern {CASC_AN_SPEC_REGEX}")
  return argValue


def getParser() -> argparse.ArgumentParser:
  # process the command line arguments
  parser = argparse.ArgumentParser(description="Synergistic Program Analyzer (SPAN)")
  subParser = parser.add_subparsers(title="subcommands", dest="subcommand",
                                    help="use ... <subcommand> -h     for more help")
  subParser.required = True

  # subcommand: analyze
  subpar = subParser.add_parser("analyze",
                                help="Non-Synergistically analyze (interactions disabled)")
  subpar.set_defaults(func=analyzeSpanIr)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("analyses", type=spanAnSpecRegex, help=analysisSpecString)
  subpar.add_argument("functionName", nargs="?",
                      help="Name of function (prefix 'f:' is optional)")
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: ianalyze
  subpar = subParser.add_parser("ianalyze",
                                help="Synergistically analyze (interactions enabled)")
  subpar.set_defaults(func=analyzeSpanIr)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("analyses", type=spanAnSpecRegex, help=analysisSpecString)
  subpar.add_argument("functionName", nargs="?",
                      help="Name of function (prefix 'f:' is optional)")
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: idemand
  subpar = subParser.add_parser("idemand",
                                help="Synergistically analyze (interactions enabled)")
  subpar.set_defaults(func=analyzeSpanIr)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("analyses", type=spanAnSpecRegex, help=analysisSpecString)
  subpar.add_argument("functionName", nargs="?",
                      help="Name of function (prefix 'f:' is optional)")
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: ipa
  subpar = subParser.add_parser("ipa",
                                help="Non-Synergistic IPA analysis (interactions disabled)")
  subpar.set_defaults(func=analyzeSpanIrIpa)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("analyses", help=analysisSpecString)
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: iipa
  subpar = subParser.add_parser("iipa",
                                help="Synergistic IPA analysis (interactions enabled)")
  subpar.set_defaults(func=analyzeSpanIrIpa)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("analyses", help=analysisSpecString)
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: cascade
  subpar = subParser.add_parser("cascade",
                                help="Simulate cascading and lerners method")
  subpar.set_defaults(func=simulateCascading)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("analyses", help=analysisSpecString)
  subpar.add_argument("functionName", nargs="?",
                      help="Name of function (prefix 'f:' is optional)")
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: demand #DDM
  subpar = subParser.add_parser("slice", help="Raise a demand to get a slice.")
  subpar.set_defaults(func=sliceDemand)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("vars", help="Comma separated vars"
                                   " e.g. 'a,b,c' (for globals specify prefix 'g:'")
  subpar.add_argument("programpoint", type=slicePointRegex,
                      help="<nodeId>['in'/'out'] e.g. 8 8in 10out (8 and 8in are same)")
  subpar.add_argument("functionName", help="Name of function (prefix 'f:' is optional)")
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: view
  subpar = subParser.add_parser("view", help="View graphs (needs xdot program)")
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("graphType",
                      choices=["cfg","cfg_nodes","callgraph","ipa-cfg"],
                      nargs="?",
                      default="cfg",
                      help="The type of graph to view")
  subpar.add_argument("functionName", nargs="?",
                      help="Name of function (prefix 'f:' is optional)")
  subpar.add_argument("fileName", help=cOrSpanirFile)
  subpar.set_defaults(func=viewDotFile)

  # subcommand: c2spanir
  subpar = subParser.add_parser("c2spanir",
                                help="Convert .c file to .c.spanir file")
  subpar.set_defaults(func=c2spanirArgParse)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: dumpir
  subpar = subParser.add_parser("dumpir",
                                help="Dump spanir after pre-processing (used for testing)")
  subpar.set_defaults(func=dumpSpanIr)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: test
  subpar = subParser.add_parser("test",
                                help="Run tests")
  subpar.set_defaults(func=testSpan)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("testType",
                      choices=["all","basic","spanir","ir","analysis"],
                      default="all")

  # subcommand: query
  subpar = subParser.add_parser("query",
                                help="Query the given translation unit for pre-defined properties")
  subpar.set_defaults(func=queryTranslationUnit)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # # subcommand: bin2mem
  # bin2memParser = subParser.add_parser("bin2mem",
  #                                      help="Binary proto format to in-memory SPAN IR")
  # bin2memParser.set_defaults(func=handleSpanIrSerialization)
  # bin2memParser.add_argument("fileName", help="Binary proto file with ext '.c.spanir.bin'")

  # # subcommand: mem2bin
  # mem2binParser = subParser.add_parser("mem2bin",
  #                                      help="In-memory SPAN IR to binary proto format")
  # mem2binParser.set_defaults(func=handleSpanIrSerialization)
  # mem2binParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: diagnose
  subpar = subParser.add_parser("diagnose",
                                help="Diagnose the program")
  subpar.set_defaults(func=diagnoseSpanIr)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("diagnosisName",
                      help="Diagnosis to run",
                      choices=getRegisteredDiagnosesList())
  subpar.add_argument("diagnosisStyle",
                      choices=["cascade","lerner","span"],
                      default="span",
                      help="The algorithm to use. (default is 'span')")
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: ipadiagnose
  subpar = subParser.add_parser("ipadiagnose",
                                help="IPA Diagnose the program")
  subpar.set_defaults(func=ipaDiagnoseSpanIr)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("diagnosisName",
                      help="Diagnosis to run",
                      choices=["interval"])
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: optimize
  subpar = subParser.add_parser("opt", help="Optimize the program")
  subpar.set_defaults(func=optimizeSpanIr)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)
  subpar.add_argument("optName",
                      choices=["all"],
                      default="all",
                      nargs="?",
                      help="Optimization to run (default is 'all')")
  subpar.add_argument("optStyle",
                      choices=["cascade","lerner","span"],
                      default="span",
                      nargs="?",
                      help="The algorithm to use. (default is 'span')")
  subpar.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: settings
  subpar = subParser.add_parser("settings", help="Current settings in SPAN.")
  subpar.set_defaults(func=dumpSpanSettings)
  subpar.add_argument('-l', '--logging', action='count', default=0)
  subpar.add_argument('-v', '--verbose', action='count', default=0)
  subpar.add_argument('-d', '--detail', action='count', default=0)
  subpar.add_argument('-c', '--check', action='count', default=0)

  return parser


