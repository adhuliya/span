#!/usr/bin/env python3.6

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
Python 3.6 or above.

This is the driver (main) module that invokes the SPAN.
This module is supposed to be aliased as `span`.

    chmod +x /<path-to-span-project>/main.py;
    sudo ln -s /<path-to-span-project>/main.py /usr/bin/span;

Once aliased, invoke `span -h` to get help with the command line options.
"""
import span.ir.callgraph
import span.util.logger as logger
import logging

import io
import os
import os.path as osp
import time
import sys
import subprocess as subp
import re
import argparse
from typing import List, Tuple
from typing import Optional as Opt
import span.util.common_util as cutil
import span.ir.types as types
import span.ir.conv as irConv
import span.sys.ddm as ddm
import span.util.consts as consts

# Initialize -- logger, etc.
if __name__ == "__main__":
  # FIXME(@PRODUCTION): change logging level to INFO or greater.
  # NOTE: span.util.util.LS also controls the logging
  logger.initLogger(appName="span", logLevel=logger.LogLevels.DEBUG)

LOG: logging.Logger = logging.getLogger("span")
LOG.info("\n\nSPAN_STARTED!\n\n")

import span.ir.tunit      as tunit
import span.ir.ir         as ir
import span.ir.util       as irUtil
import span.api.analysis  as an
import span.ir.ipa        as irIpa
import span.ir.query      as irQuery

import span.util.util     as util

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
  cutil.Verbosity = args.verbose
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
        f" {cFileName} 2> /dev/null"

  print("running> ", cmd)
  completed = subp.run(cmd, shell=True)
  print("SPAN: clang return code:", completed.returncode)
  if completed.returncode != 0:
    print("SPAN: ERROR.")
    print("Maybe an invalid C program!")
    print("Try compiling the input program first, to check its validity.")
    return completed.returncode
  return 0


def ipaDiagnoseSpanIr(args: argparse.Namespace) -> None:
  diName    = args.diagnosisName
  fileName = args.fileName
  cutil.Verbosity = args.verbose

  spanirFileName = convertIfCFile(fileName)
  print("Filename:", fileName, spanirFileName)
  currTUnit = parseTUnitObject(spanirFileName, ipa=True)

  if diName == "interval":
    sysIpa.diagnoseInterval(currTUnit)
  else:
    raise ValueError(f"Unknown diagnosis name: {diName}")


def optimizeSpanIr(args: argparse.Namespace) -> None:
  optName = args.optName
  cutil.Verbosity = args.verbose

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
  cutil.Verbosity = args.verbose

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
  print("Return Code:", completed.returncode)
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
      raise ValueError(f"No analysis: {onlyAnName}")

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
      raise ValueError(f"Error in analysis expr: f{anNamesExpr}")

  maxAnalysisCount = max(analysisCount, maxAnalysisCount)

  return mainAnalysis, otherAnalyses, supportAnalyses, avoidAnalyses, maxAnalysisCount


def parseCascadingAnalysisExpr(anNameExpr: str) -> Tuple[str, list, list, int]:
  """Parse the analysis expression as specified by
  `SPAN_AN_SPEC_REGEX` (for cascading/lerner) and return the result."""
  mainAnalysis      = ""
  otherAnalyses     = []
  avoidAnalyses     = []
  maxAnalysisCount  = 1024 # a large number

  if anNameExpr[0] == "/" and anNameExpr[-1] == "/":
    maxAnalysisCount = 0
    if anNameExpr[0] == "/" and anNameExpr[-1] != "/" or \
        anNameExpr[0] != "/" and anNameExpr[-1] == "/":
      exit(20)
    anNameExpr = anNameExpr[1:-1]

  givenAnalyses = re.findall(r"[+-]\w+", anNameExpr)

  for anName in givenAnalyses:
    prefix = anName[0]
    onlyAnName = anName[1:]
    if onlyAnName not in clients.analyses:
      raise ValueError(f"No analysis: {onlyAnName}")
    if prefix == "+":
      maxAnalysisCount += 1
      if not mainAnalysis:
        mainAnalysis = onlyAnName
      else:
        otherAnalyses.append(onlyAnName)
    elif anName[0] == "-":
      avoidAnalyses.append(onlyAnName)
    else:
      raise ValueError(f"Error in analysis expr: f{anNameExpr}")

  return mainAnalysis, otherAnalyses, avoidAnalyses, maxAnalysisCount


def analyzeSpanIrIpa(args: argparse.Namespace) -> None:
  """Runs the given analyses on the whole spanir translation unit."""
  disableAllSim = True if args.subcommand == "ipa" else False
  cutil.Verbosity = args.verbose

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

  timer = cutil.Timer()
  ipa1.analyze()
  print("OnlyAnalysis:", timer.stop())


def analyzeSpanIr(args: argparse.Namespace) -> None:
  """Runs the given analyses on the spanir file for each function."""
  disableAllSim = True if args.subcommand == "analyze" else False
  cutil.Verbosity = args.verbose
  idemand = True if args.subcommand == "idemand" else False

  anNameExpr = args.analyses
  funcName = args.functionName

  funcName = None if not funcName else irConv.canonicalizeFuncName(funcName)
  print("Analyzing Function(s):", funcName if funcName else "ALL")

  mainAnalysis, otherAnalyses, supportAnalyses, avoidAnalyses, maxAnalysisCount = \
    parseSpanAnalysisExpr(anNameExpr)

  currTUnit = parseTUnitObject(args.fileName)

  if funcName is not None and funcName not in currTUnit.allFunctions:
    print(f"SPAN: ERROR: {funcName} not found.", file=sys.stderr)
    exit(42)

  timer = cutil.Timer("SpanAnalysis(with setups)")
  analysisTime = analyzeFunctions(currTUnit=currTUnit,
                                  funcName=funcName,
                                  mainAnName=mainAnalysis,
                                  otherAnalyses=otherAnalyses,
                                  supportAnalyses=supportAnalyses,
                                  avoidAnalyses=avoidAnalyses,
                                  maxNumOfAnalyses=maxAnalysisCount,
                                  disableAllSim=disableAllSim,
                                  useDdm=idemand)
  timer.stopAndLog()
  print(f"TimeElapsed(SpanAnalysis(no   setups)): {analysisTime} ms")


def analyzeFunctions(
    currTUnit: tunit.TranslationUnit,
    funcName: Opt[types.FuncNameT],
    mainAnName: Opt[an.AnalysisNameT] = None,
    otherAnalyses: Opt[List[an.AnalysisNameT]] = None,
    supportAnalyses: Opt[List[an.AnalysisNameT]] = None,
    avoidAnalyses: Opt[List[an.AnalysisNameT]] = None,
    maxNumOfAnalyses: int = 1024,
    analysisSeq: Opt[List[List[an.AnalysisNameT]]] = None,  # for cascading/lerner
    disableAllSim: bool = False,
    useDdm: bool = False,
) -> float: # returns total analysis time (only) in milliseconds
  totalAnalysisTime: float = 0

  for func in currTUnit.yieldFunctionsWithBody():
    if funcName and not funcName == func.name:
      continue
    print("\nAnalyzingFunction:", func.name)
    syn1 = host.Host(
      func              = func,
      mainAnName        = mainAnName,
      otherAnalyses     = otherAnalyses,
      supportAnalyses   = supportAnalyses,
      avoidAnalyses     = avoidAnalyses,
      maxNumOfAnalyses  = maxNumOfAnalyses,
      analysisSeq       = analysisSeq,
      disableAllSim     = disableAllSim,
      useDdm            = useDdm,
    )
    analysisTime = syn1.analyze() # do the analysis
    totalAnalysisTime += analysisTime
    print("HostObjectSize (after  analysis):", cutil.getSize2(syn1))
    print("========================================")
    syn1.printOrLogResult() # print the result of each analysis

  return totalAnalysisTime


def queryTranslationUnit(args: argparse.Namespace):
  """Query predefined information on the translation unit."""
  fileName = args.fileName
  cutil.Verbosity = args.verbose
  currTUnit = parseTUnitObject(fileName)

  irQuery.executeAllQueries(currTUnit)


def viewDotFile(args: argparse.Namespace):
  """Generates the dot files to view the IR better."""
  graphType = args.graphType
  fileName = args.fileName
  cutil.Verbosity = args.verbose

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
  if not cutil.programExists("xdot"):
    print(installDotMsg)
    return False
  else:
    util.exitIfProgramDoesnotExist("xdot")
    cmd = f"xdot {dotFileName} &"
    print("running>", cmd)
    completed = subp.run(cmd, shell=True)
    print("SPAN: xdot return Code:", completed.returncode)
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
  """Invokes the unit and functional tests.
  It first checks if the current directory has test cases.
  """
  testType = args.testType
  cutil.Verbosity = args.verbose

  import span.tests.run as run
  run.runTests(testType)


def getCmdLineFuncName(funcName: Opt[types.FuncNameT]) -> Opt[types.FuncNameT]:
  return None if not funcName else irConv.canonicalizeFuncName(funcName)


def sliceDemand(args: argparse.Namespace):
  """Raises demand as provided in args."""
  ppPattern = re.compile(SLICE_POINT_REGEX)
  programPoint = args.programpoint
  vars = args.vars
  cutil.Verbosity = args.verbose

  funcName = getCmdLineFuncName(args.functionName)
  assert funcName, f"{args.functionName}"
  print("Using Function(s):", funcName if funcName else "ALL")

  currTUnit = parseTUnitObject(args.fileName)
  func = currTUnit.getFuncObj(funcName)

  m = ppPattern.match(programPoint)
  assert m, f"{programPoint}"
  nid = int(m.group(1))
  assert func.cfg, f"{func}"
  node = func.cfg.nodeMap[nid]
  atIn = True if not m.group(2) else m.group(2).lower() == "in"
  varSet = frozenset(irConv.genLocalName(func.name, var) for var in vars.split(","))

  print("Note: Assuming all nodes are feasible.")
  ddMethod = ddm.DdMethod(func)
  for varName in varSet:
    demand = ddm.AtomicDemand(func, node, atIn, varName,
                              ir.inferTypeOfVal(func, varName), irConv.Backward)
    print("Got Slice:", ddMethod.propagateDemand(demand))
    print("InfeasibleNodeDependence:", ddMethod.infNodeDep)


def simulateCascading(args: argparse.Namespace):
  """Runs the cascaded analyses on the spanir file for each function."""
  anNameExpr = args.analyses
  cutil.Verbosity = args.verbose

  funcName = getCmdLineFuncName(args.functionName)
  print("Analyzing Function(s):", funcName if funcName else "ALL")

  stepPattern = re.compile(r"/.*?/")
  allSteps = stepPattern.findall(anNameExpr)
  analysisSeq: List[List[an.AnalysisNameT]] = []

  for step in allSteps:
    mainAnalysis, otherAnalyses, _, _ = parseCascadingAnalysisExpr(step)
    analysisSeq.append([mainAnalysis])
    analysisSeq.append(otherAnalyses)

  currTUnit = parseTUnitObject(args.fileName)

  timer = cutil.Timer("CascadingAnalysis")
  analyzeFunctions(currTUnit=currTUnit,
                   funcName=funcName,
                   analysisSeq=analysisSeq)
  timer.stopAndLog()


def dumpSpanIr(args: argparse.Namespace):
  """Dumps the pre-processed SPAN IR to the given file
  suffixed with `.spanir.processed` suffix.
  (used for testing purposes)
  Eg. for `test.c` or `test.c.spanir`, it generates
  `test.c.spanir.processed`
  """
  fileName = args.fileName
  cutil.Verbosity = args.verbose

  spanIrFileName = convertIfCFile(fileName)
  cFileName = extractCFileName(spanIrFileName)
  if not cFileName:
    exit(19)

  currTUnit: tunit.TranslationUnit = ir.readSpanIr(spanIrFileName)

  processedSpanIrString = repr(currTUnit)
  outFileName = f"{spanIrFileName}.processed"
  util.writeToFile(outFileName, processedSpanIrString)


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
  timer = cutil.Timer("ParseTranslationUnit")
  spanIrFileName  = convertIfCFile(fileName)
  cFileName       = extractCFileName(spanIrFileName)
  if not cFileName: exit(19)

  currTUnit: tunit.TranslationUnit = ir.readSpanIr(spanIrFileName)
  if ipa: irIpa.preProcess(currTUnit)

  timer.stopAndLog()
  print("TUnitObjSize:", cutil.getSize2(currTUnit))
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

# mainentry - when this module is run
if __name__ == "__main__":
  print("SPAN is:", os.path.realpath(__file__))
  # sys.setrecursionlimit(10000) # FIXME: It is needed in some cases. But why exactly?
  print("RotatingLogFile: file://", logger.ABS_LOG_FILE_NAME, sep="")

  analysisSpecString = f"Specification of analyses" \
                       f" to run choose from {getRegisteredAnalyses()}"
  cOrSpanirFile = "The .c or .spanir file."

  # process the command line arguments
  parser = argparse.ArgumentParser(description="Synergistic Program Analyzer (SPAN)")
  subParser = parser.add_subparsers(title="subcommands", dest="subcommand",
                                    help="use ... <subcommand> -h     for more help")
  subParser.required = True

  # subcommand: analyze
  analyzeParser = subParser.add_parser("analyze",
                                       help="Non-Synergistically analyze (interactions disabled)")
  analyzeParser.set_defaults(func=analyzeSpanIr)
  analyzeParser.add_argument('-v', '--verbose', action='count', default=0)
  analyzeParser.add_argument("analyses", type=spanAnSpecRegex, help=analysisSpecString)
  analyzeParser.add_argument("functionName", nargs="?",
                             help="Name of function (prefix 'f:' is optional)")
  analyzeParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: ianalyze
  ianalyzeParser = subParser.add_parser("ianalyze",
                                        help="Synergistically analyze (interactions enabled)")
  ianalyzeParser.set_defaults(func=analyzeSpanIr)
  ianalyzeParser.add_argument('-v', '--verbose', action='count', default=0)
  ianalyzeParser.add_argument("analyses", type=spanAnSpecRegex, help=analysisSpecString)
  ianalyzeParser.add_argument("functionName", nargs="?",
                              help="Name of function (prefix 'f:' is optional)")
  ianalyzeParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: idemand
  ianalyzeParser = subParser.add_parser("idemand",
                                        help="Synergistically analyze (interactions enabled)")
  ianalyzeParser.set_defaults(func=analyzeSpanIr)
  ianalyzeParser.add_argument('-v', '--verbose', action='count', default=0)
  ianalyzeParser.add_argument("analyses", type=spanAnSpecRegex, help=analysisSpecString)
  ianalyzeParser.add_argument("functionName", nargs="?",
                              help="Name of function (prefix 'f:' is optional)")
  ianalyzeParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: ipa
  ianalyzeParser = subParser.add_parser("ipa",
                                        help="Non-Synergistic IPA analysis (interactions disabled)")
  ianalyzeParser.set_defaults(func=analyzeSpanIrIpa)
  ianalyzeParser.add_argument('-v', '--verbose', action='count', default=0)
  ianalyzeParser.add_argument("analyses", help=analysisSpecString)
  ianalyzeParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: iipa
  ianalyzeParser = subParser.add_parser("iipa",
                                        help="Synergistic IPA analysis (interactions enabled)")
  ianalyzeParser.set_defaults(func=analyzeSpanIrIpa)
  ianalyzeParser.add_argument('-v', '--verbose', action='count', default=0)
  ianalyzeParser.add_argument("analyses", help=analysisSpecString)
  ianalyzeParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: cascade
  cascadeParser = subParser.add_parser("cascade",
                                        help="Simulate cascading and lerners method")
  cascadeParser.set_defaults(func=simulateCascading)
  cascadeParser.add_argument('-v', '--verbose', action='count', default=0)
  cascadeParser.add_argument("analyses", help=analysisSpecString)
  cascadeParser.add_argument("functionName", nargs="?",
                              help="Name of function (prefix 'f:' is optional)")
  cascadeParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: demand #DDM
  sliceParser = subParser.add_parser("slice", help="Raise a demand to get a slice.")
  sliceParser.set_defaults(func=sliceDemand)
  sliceParser.add_argument('-v', '--verbose', action='count', default=0)
  sliceParser.add_argument("vars", help="Comma separated vars"
                                        " e.g. 'a,b,c' (for globals specify prefix 'g:'")
  sliceParser.add_argument("programpoint", type=slicePointRegex,
                           help="<nodeId>['in'/'out'] e.g. 8 8in 10out (8 and 8in are same)")
  sliceParser.add_argument("functionName", help="Name of function (prefix 'f:' is optional)")
  sliceParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: view
  viewParser = subParser.add_parser("view", help="View graphs (needs xdot program)")
  viewParser.add_argument("graphType",
                          choices=["cfg","cfg_nodes","callgraph","ipa-cfg"],
                          nargs="?",
                          default="cfg",
                          help="The type of graph to view")
  viewParser.add_argument("functionName", nargs="?",
                          help="Name of function (prefix 'f:' is optional)")
  viewParser.add_argument("fileName", help=cOrSpanirFile)
  viewParser.set_defaults(func=viewDotFile)
  viewParser.add_argument('-v', '--verbose', action='count', default=0)

  # subcommand: c2spanir
  c2SpanirParser = subParser.add_parser("c2spanir",
                                        help="Convert .c file to .c.spanir file")
  c2SpanirParser.set_defaults(func=c2spanirArgParse)
  c2SpanirParser.add_argument('-v', '--verbose', action='count', default=0)
  c2SpanirParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: dumpir
  c2SpanirParser = subParser.add_parser("dumpir",
                                        help="Dump spanir after pre-processing (used for testing)")
  c2SpanirParser.set_defaults(func=dumpSpanIr)
  c2SpanirParser.add_argument('-v', '--verbose', action='count', default=0)
  c2SpanirParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: test
  testParser = subParser.add_parser("test",
                                    help="Run tests")
  testParser.set_defaults(func=testSpan)
  testParser.add_argument('-v', '--verbose', action='count', default=0)
  testParser.add_argument("testType",
                          choices=["all","basic","spanir","ir","analysis"],
                          default="all")

  # subcommand: query
  ianalyzeParser = subParser.add_parser("query",
                                        help="Query the given translation unit for pre-defined properties")
  ianalyzeParser.set_defaults(func=queryTranslationUnit)
  ianalyzeParser.add_argument('-v', '--verbose', action='count', default=0)
  ianalyzeParser.add_argument("fileName", help=cOrSpanirFile)

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
  diagnoseParser = subParser.add_parser("diagnose",
                                       help="Diagnose the program")
  diagnoseParser.set_defaults(func=diagnoseSpanIr)
  diagnoseParser.add_argument('-v', '--verbose', action='count', default=0)
  diagnoseParser.add_argument("diagnosisName",
                              help="Diagnosis to run",
                              choices=getRegisteredDiagnosesList())
  diagnoseParser.add_argument("diagnosisStyle",
                              choices=["cascade","lerner","span"],
                              default="span",
                              help="The algorithm to use. (default is 'span')")
  diagnoseParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: ipadiagnose
  ipaDiagnoseParser = subParser.add_parser("ipadiagnose",
                                        help="IPA Diagnose the program")
  ipaDiagnoseParser.set_defaults(func=ipaDiagnoseSpanIr)
  ipaDiagnoseParser.add_argument('-v', '--verbose', action='count', default=0)
  ipaDiagnoseParser.add_argument("diagnosisName",
                              help="Diagnosis to run",
                              choices=["interval"])
  ipaDiagnoseParser.add_argument("fileName", help=cOrSpanirFile)

  # subcommand: optimize
  optParser = subParser.add_parser("opt", help="Optimize the program")
  optParser.set_defaults(func=optimizeSpanIr)
  optParser.add_argument("optName",
                         choices=["all"],
                         default="all",
                         nargs="?",
                         help="Optimization to run (default is 'all')")
  optParser.add_argument("optStyle",
                         choices=["cascade","lerner","span"],
                         default="span",
                         nargs="?",
                         help="The algorithm to use. (default is 'span')")
  optParser.add_argument('-v', '--verbose', action='count', default=0)
  optParser.add_argument("fileName", help=cOrSpanirFile)

  try: # TODO: add auto completion if present
    # ref: https://stackoverflow.com/questions/14597466/custom-tab-completion-in-python-argparse
    import argcomplete  # type: ignore
    argcomplete.autocomplete(parser)
  except:
    pass

  args = parser.parse_args()  # parse command line

  timer = cutil.Timer("TotalTimeTaken")
  args.func(args)             # take action
  timer.stopAndLog()

  LOG.info("FINISHED!")  # type: ignore

