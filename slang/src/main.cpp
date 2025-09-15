// Example invocation:
// ./slang test_prog_00.c -p compile_commands.json

// Generate the SPAN IR from Clang AST.

#include "clang/Basic/Version.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/AST/ASTTypeTraits.h"
#include "clang/AST/ParentMapContext.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendAction.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"

#include "llvm/Support/CommandLine.h"
#include "llvm/ADT/SmallVector.h"

#include <fstream>        //for std::ofstream
#include <iomanip>        //for std::fixed
#include <sstream>        //for std::stringstream
#include <string>         //for std::string
#include <unordered_map>  //for std::unordered_map
#include <utility>        //for std::pair
#include <vector>         //for std::vector
#include "spir.pb.h"      //for BitTU and other protobuf classes
#include "util.h"         //for Util::writeToFile

using namespace clang::tooling;
using namespace clang;

#define K_00_GLBL_INIT_FUNC_NAME "f:00_glbl_init:optional,comma,separated,flags"
#define K_00_GLBL_INIT_FUNC_ID 1

static llvm::cl::OptionCategory SlangOptions("slang options");

static llvm::cl::opt<std::string> OptOutputDir(
    "o",
    llvm::cl::desc("Must specify output directory for output."
    " The .spir extension is automatically added to each output file."),
    llvm::cl::value_desc("directory"),
    llvm::cl::cat(SlangOptions));

// Command line option for protobuf output
static llvm::cl::opt<bool> OptProtoOutputKnob(
    "proto",
    llvm::cl::desc("Output SPAN IR in protobuf format (default: true)"),
    llvm::cl::init(true),
    llvm::cl::cat(SlangOptions));

// Command line option for Python SPAN IR output
static llvm::cl::opt<bool> OptPySpanIrOutputKnob(
    "py-spanir", 
    llvm::cl::desc("Output SPAN IR in Python format (default: false)"),
    llvm::cl::init(false),
    llvm::cl::cat(SlangOptions));

namespace spir {

typedef std::vector<const Stmt *> StmtVector;
typedef std::vector<std::string> SpanStmtVector;

// non-breaking space
#define NBSP1 " "
#define NBSP2 NBSP1 NBSP1
#define NBSP4 NBSP2 NBSP2
#define NBSP6 NBSP2 NBSP4
#define NBSP8 NBSP4 NBSP4
#define NBSP10 NBSP4 NBSP6
#define NBSP12 NBSP6 NBSP6

#define VAR_NAME_PREFIX "v:"
#define GLOBAL_VAR_NAME_PREFIX "g:"
#define FUNC_NAME_PREFIX "f:"

#define DONT_PRINT "DONT_PRINT"
#define NULL_STMT "NULL_STMT"

#define LABEL_PREFIX "instr.LabelI(\""
#define LABEL_SUFFIX "\")"

// the numbering 0,1,2 is important.
enum EdgeLabel { FalseEdge = 0, TrueEdge = 1, UnCondEdge = 2 };
enum SlangRecordKind { Struct = 0, Union = 1 };

class SlangExpr {
public:
  std::string expr;
  bool compound;
  std::string locStr;
  QualType qualType;
  bool nonTmpVar;
  uint64_t varId;

  SlangExpr() {
    expr = "";
    compound = false;
    locStr = "";
    qualType = QualType();
    nonTmpVar = true;
    varId = 0;
  };

  std::string toString() {
    std::stringstream ss;
    ss << "SlangExpr:\n";
    ss << "  Expr     : " << expr << "\n";
    ss << "  ExprType : " << qualType.getAsString() << "\n";
    ss << "  NonTmpVar: " << (nonTmpVar ? "true" : "false") << "\n";
    ss << "  VarId    : " << varId << "\n";

    return ss.str();
  }
};

class SlangVar {
public:
  uint64_t id;
  // variable name: e.g. a variable 'x' in main function, is "v:main:x".
  std::string name;
  std::string typeStr;

  SlangVar() {}

  SlangVar(uint64_t id, std::string name) {
    // specially for anonymous member names (needed in member expressions)
    this->id = id;
    this->name = name;
    this->typeStr = DONT_PRINT;
  }

  std::string convertToString() {
    std::stringstream ss;
    ss << "\"" << name << "\": " << typeStr << ",";
    return ss.str();
  }

  void setLocalVarName(std::string varName, std::string funcName) {
    name = VAR_NAME_PREFIX;
    name += funcName + ":" + varName;
  }

  void setLocalVarNameStatic(std::string varName, std::string funcName) {
    name = GLOBAL_VAR_NAME_PREFIX;
    name += funcName + ":" + varName;
  }

  void setGlobalVarName(std::string varName) {
    name = GLOBAL_VAR_NAME_PREFIX;
    name += varName;
  }
}; // class SlangVar

// holds info of a single function
class SlangFunc {
public:
  std::string name;     // e.g. 'main'
  std::string fullName; // e.g. 'f:main'
  std::string retType;
  std::vector<std::string> paramNames;
  bool variadic;

  uint32_t tmpVarCount;

  SpanStmtVector spanStmts;
  bool hasBody;

  SlangFunc() {
    variadic = false;
    paramNames = std::vector<std::string>{};
    tmpVarCount = 0;
    hasBody = false;
  }
}; // class SlangFunc

class SlangRecord;

class SlangRecordField {
public:
  bool anonymous;
  std::string name;
  std::string typeStr;
  SlangRecord *slangRecord;
  QualType type;

  SlangRecordField()
      : anonymous{false}, name{""}, typeStr{""}, type{QualType()} {}

  std::string getName() const { return name; }

  std::string toString() {
    std::stringstream ss;
    ss << "("
       << "\"" << name << "\"";
    ss << ", " << typeStr << ")";
    return ss.str();
  }

  void clear() {
    anonymous = false;
    name = "";
    typeStr = "";
    type = QualType();
  }
}; // class SlangRecordField

// holds a struct or a union record
class SlangRecord {
public:
  SlangRecordKind recordKind; // Struct, or Union
  bool anonymous;
  std::string name;
  std::vector<SlangRecordField> members;
  std::string locStr;
  int32_t nextAnonymousFieldId;

  SlangRecord() {
    recordKind = Struct; // Struct, or Union
    anonymous = false;
    name = "";
    nextAnonymousFieldId = 0;
  }

  std::string getNextAnonymousFieldIdStr() {
    std::stringstream ss;
    nextAnonymousFieldId += 1;
    ss << nextAnonymousFieldId;
    return ss.str();
  }

  std::vector<SlangRecordField> getFields() const { return members; }

  std::string getMemberName(int index) const { return members[index].name; }

  void genMemberAccessExpr(std::string &of, std::string &loc, int index,
                           SlangExpr &slangExpr) {
    std::stringstream ss;

    ss << "expr.MemberE(\"" << getMemberName(index) << "\"";
    ss << ", " << of;
    ss << ", " << loc << ")"; // end expr.MemberE(

    slangExpr.expr = ss.str();
    slangExpr.qualType = members[index].type;
  }

  std::string genMemberExpr(std::vector<uint32_t> indexVector) {
    std::stringstream ss;

    std::vector<std::string> members;
    SlangRecord *currentRecord = this;
    llvm::errs() << "\n------------------------\n"
                 << currentRecord->members.size() << "\n";
    llvm::errs() << "\n------------------------\n"
                 << indexVector.size() << "\n";
    llvm::errs() << "\n------------------------\n"
                 << indexVector[0] << indexVector[1] << "\n";
    llvm::errs().flush();
    for (auto it = indexVector.begin(); it != indexVector.end(); ++it) {
      members.push_back(currentRecord->members[*it].name);
      if (currentRecord->members[*it].slangRecord != nullptr) {
        // means its a member of type record
        currentRecord = currentRecord->members[*it].slangRecord;
      }
    }

    std::string prefix = "";
    for (auto it = members.end() - 1; it != members.begin() - 1; --it) {
      ss << prefix << "expr.MemberE(\"" << *it << "\"";
      if (prefix == "") {
        prefix = ", ";
      }
    }

    return ss.str();
  }

  std::string toString() {
    std::stringstream ss;
    ss << NBSP6;
    ss << ((recordKind == Struct) ? "types.Struct(\n" : "types.Union(\n");

    ss << NBSP8 << "name = ";
    ss << "\"" << name << "\""
       << ",\n";

    std::string suffix = ",\n";
    ss << NBSP8 << "members = [\n";
    for (auto member : members) {
      ss << NBSP10 << member.toString() << suffix;
    }
    ss << NBSP8 << "],\n";

    ss << NBSP8 << "info = " << locStr << ",\n";
    ss << NBSP6 << ")"; // close types.*(...

    return ss.str();
  }

  std::string toShortString() {
    std::stringstream ss;

    if (recordKind == Struct) {
      ss << "types.Struct";
    } else {
      ss << "types.Union";
    }
    ss << "(\"" << name << "\")";

    return ss.str();
  }
}; // class SlangRecord

// holds info about the switch-cases
class SwitchCtrlFlowLabels {
public:
  int counter;
  std::string switchStrId;       // id for the switch
  std::string thisCaseCondLabel; // label for the current case
  std::string thisBodyLabel;     // label for the current body
  std::string nextCaseCondLabel; // label for the next case (when encountered)
  std::string nextBodyLabel;     // label for the next body (case or default)
  std::string switchStartLabel;  // switch start label
  std::string switchExitLabel;   // switch exit label
  std::string defaultCaseLabel;
  std::string gotoLabel;       // a label
  std::string gotoLabelLocStr; // a label
  SlangExpr switchCond;
  std::stringstream ss;
  bool defaultExists;

  SwitchCtrlFlowLabels(std::string id) {
    switchStrId = id;
    counter = 0;
    defaultExists = false;
    switchStartLabel = switchStrId + "SwitchStart";
    switchExitLabel = switchStrId + "SwitchExit";
    defaultCaseLabel = switchStrId + "Default";
    thisCaseCondLabel = ""; // initially no condition
    thisBodyLabel = "";     // initially no body
    auto count = getNextCounterStr();
    nextCaseCondLabel = genLabel("CaseCond", count);
    nextBodyLabel = genLabel("CaseBody", count);
    gotoLabel = "";
    gotoLabelLocStr = "";
  }

  void setupForThisCase() {
    thisCaseCondLabel = nextCaseCondLabel;
    thisBodyLabel = nextBodyLabel;
    auto count = getNextCounterStr();
    nextCaseCondLabel = genLabel("CaseCond", count);
    nextBodyLabel = genLabel("CaseBody", count);
  }

  void setupForDefaultCase() {
    defaultExists = true;
    thisCaseCondLabel = defaultCaseLabel;
    thisBodyLabel = nextBodyLabel;
    auto count = getNextCounterStr();
    // nextCaseCondLabel = genLabel("CaseCond", count); // deliberatly commented
    nextBodyLabel = genLabel("CaseBody", count);
  }

  std::string getNextCounterStr() {
    std::stringstream ss;
    counter += 1;
    ss << counter;
    return ss.str();
  }

  std::string genLabel(std::string s, std::string count) {
    std::stringstream ss;
    ss << switchStrId << s << count;
    return ss.str();
  }
}; // class SwitchCtrlFlowLabels

// holds details of the entire translation unit
class SlangTranslationUnit {
public:
  std::string tuName; // the current translation unit file name
  std::string tuDirectory; // the current translation unit directory
  BitTU bittu; // the bit translation unit

  SpanStmtVector globalInits; // global variable initializations

  SlangFunc *currFunc; // the current function being translated
  uint64_t uniqIdCounter; // used to generate unique ids for tmp variables etc.
  uint32_t uniqLabelCounter; // used to generate unique labels
  uint32_t uniqRecordIdCounter; // to generate unique ids for anonymous records

  // maps a unique variable id (address of AST node) to its SlangVar.
  std::unordered_map<uint64_t, SlangVar> varMap;
  // map of var-name to a count:
  // used in case two local variables have same name (blocks)
  std::unordered_map<std::string, uint64_t> varCountMap;
  // contains functions
  std::unordered_map<uint64_t, SlangFunc> funcMap;
  // contains structs
  std::unordered_map<uint64_t, SlangRecord> recordMap;

  // tracks variables that become dirty in an expression
  std::unordered_map<uint64_t, SlangExpr> dirtyVars;

  // vector of start and exit label of constructs which can contain break and
  // continue stmts.
  std::vector<std::pair<std::string, std::string>> entryExitLabels;

  // to handle the conversion of switch statements
  SwitchCtrlFlowLabels *switchCfls;

  // is static local var decl?
  bool isStaticLocal;

  void pushLabels(std::string entry, std::string exit) {
    auto labelPair = std::make_pair(entry, exit);
    entryExitLabels.push_back(labelPair);
  }

  void popLabel() { entryExitLabels.pop_back(); }

  std::pair<std::string, std::string> &peekLabel() {
    return entryExitLabels[entryExitLabels.size() - 1];
  }

  std::string peekEntryLabel() {
    return entryExitLabels[entryExitLabels.size() - 1].first;
  }

  std::string peekExitLabel() {
    return entryExitLabels[entryExitLabels.size() - 1].second;
  }

  SlangTranslationUnit()
      : uniqIdCounter{0}, tuName{}, tuDirectory{}, bittu{}, globalInits{}, 
        currFunc{nullptr}, uniqRecordIdCounter{0}, varMap{}, varCountMap{}, funcMap{},
        dirtyVars{}, switchCfls{nullptr}, isStaticLocal{false} {}

  // clear the buffer for the next function.
  void clear() {
    varMap.clear();
    dirtyVars.clear();
    varCountMap.clear();
  } // clear()

  uint32_t genNextLabelCount() {
    uniqLabelCounter += 1;
    return uniqLabelCounter;
  }

  std::string genNextLabelCountStr() {
    std::stringstream ss;
    ss << genNextLabelCount();
    return ss.str();
  }

  void addStmt(std::string spanStmt) {
    if (isStaticLocal) {
      auto func = &funcMap[0];
      func->spanStmts.push_back(spanStmt);
    } else {
      currFunc->spanStmts.push_back(spanStmt);
    }
  }

  void addStmtBit(BitInsn* bitInsn) {
    if (isStaticLocal) {
      bittu.mutable_functions()[0].mutable_insns()->AddAllocated(bitInsn);
    } else {
      currentBitFunc->mutable_insns()->AddAllocated(bitInsn);
    }
  }

  void pushBackFuncParams(std::string paramName) {
    SLANG_TRACE("AddingParam: " << paramName << " to func " << currFunc->name)
    currFunc->paramNames.push_back(paramName);
  }

  void setFuncReturnType(std::string &retType) { currFunc->retType = retType; }

  void setVariadicness(bool variadic) { currFunc->variadic = variadic; }

  std::string getCurrFuncName() {
    return currFunc->name; // not fullName
  }

  SlangVar &getVar(uint64_t varAddr) {
    // FIXME: there is no check
    return varMap[varAddr];
  }

  bool isNewVar(uint64_t varAddr) {
    return varMap.find(varAddr) == varMap.end();
  }

  uint32_t nextTmpId() {
    currFunc->tmpVarCount += 1;
    return currFunc->tmpVarCount;
  }

  uint64_t nextUniqueId() {
    uniqIdCounter += 1;
    return uniqIdCounter;
  }

  void addVar(uint64_t varId, SlangVar &slangVar) { varMap[varId] = slangVar; }

  void addVarBit(uint64_t eid, BitEntityInfo* bitEntityInfo) {
    bittu.mutable_namestoids()->emplace(bitEntityInfo->strval(), eid);
    bittu.mutable_entityinfo()->emplace(eid, *bitEntityInfo);
  }

  bool isRecordPresent(uint64_t recordAddr) {
    return !(recordMap.find(recordAddr) == recordMap.end());
  }

  bool isRecordPresentBit(uint64_t recordAddr) {
    return bittu.entityinfo().find(recordAddr) != bittu.entityinfo().end();
  }

  void addRecord(uint64_t recordAddr, SlangRecord slangRecord) {
    recordMap[recordAddr] = slangRecord;
  }

  SlangRecord &getRecord(uint64_t recordAddr) { return recordMap[recordAddr]; }

  int32_t getNextRecordId() {
    uniqRecordIdCounter += 1;
    return uniqRecordIdCounter;
  }

  std::string getNextRecordIdStr() {
    std::stringstream ss;
    ss << getNextRecordId();
    return ss.str();
  }

  std::string convertFuncName(std::string funcName) {
    std::stringstream ss;
    ss << FUNC_NAME_PREFIX << funcName;
    return ss.str();
  }

  std::string convertVarExpr(uint64_t varAddr) {
    // if here, var should already be in varMap
    std::stringstream ss;

    auto slangVar = varMap[varAddr];
    ss << slangVar.name;

    return ss.str();
  }

  uint64_t convertVarExprBit(uint64_t varAddr) {
    // if here, var should already be known
    return varAddr; 
  }


  // BOUND START: dump_routines (to SPAN Strings)

  // Function to get output filename or error out
  std::string getOutFilename(std::string suffix) {
    // If output directory is specified, use it, otherwise use current directory
    std::string outDir = OptOutputDir.empty() ? std::string(".") : OptOutputDir;

    // Build full path by combining output directory, tuName and suffix
    std::string fullPath = outDir + "/" + tuName + suffix;

    SLANG_INFO("Outputting to: " << fullPath)
      
    return fullPath;
  };

  // dump entire span ir module for the translation unit.
  void dumpSlangIr() {
    // Write the bit translation unit to a file
    if (OptProtoOutputKnob) {
      writeProtoToFile(bittu, getOutFilename(".spir"));
    }

    if (!OptPySpanIrOutputKnob) {
      return;
    }

    std::stringstream ss;

    dumpHeader(ss);
    dumpVariables(ss);
    dumpGlobalInits(ss);
    dumpObjs(ss);
    dumpFooter(ss);

    if (this->tuName.size()) {
      slang::Util::writeToFile(getOutFilename(".spanir.py"), ss.str());
    } else {
      SLANG_INFO("FILE_HAS_NO_FUNCTION: Hence no output spanir file.")
    }
  } // dumpSlangIr()

  void dumpHeader(std::stringstream &ss) {
    ss << "\n";
    ss << "# START: A_SPAN_translation_unit!\n";
    ss << "\n";
    ss << "# eval() the contents of this file.\n";
    ss << "# Keep the following imports in effect when calling eval.\n";
    ss << "\n";
    ss << "# import span.ir.types as types\n";
    ss << "# import span.ir.op as op\n";
    ss << "# import span.ir.expr as expr\n";
    ss << "# import span.ir.instr as instr\n";
    ss << "# import span.ir.constructs as constructs\n";
    ss << "# import span.ir.tunit as tunit\n";
    ss << "# from span.ir.types import Loc\n";
    ss << "\n";
    ss << "# An instance of span.ir.tunit.TranslationUnit class.\n";
    ss << "tunit.TranslationUnit(\n";
    ss << NBSP2 << "name = \"" << tuName << "\",\n";
    ss << NBSP2 << "description = \"Auto-Translated from Clang AST.\",\n";
  } // dumpHeader()

  void dumpFooter(std::stringstream &ss) {
    ss << ") # tunit.TranslationUnit() ends\n";
    ss << "\n# END  : A_SPAN_translation_unit!\n";
  } // dumpFooter()

  void dumpVariables(std::stringstream &ss) {
    ss << "\n";
    ss << NBSP2 << "allVars = {\n";
    for (const auto &var : varMap) {
      if (var.second.typeStr == DONT_PRINT)
        continue;
      ss << NBSP4;
      ss << "\"" << var.second.name << "\": " << var.second.typeStr << ",\n";
    }
    ss << NBSP2 << "}, # end allVars dict\n\n";
  } // dumpVariables()

  void dumpGlobalInits(std::stringstream &ss) {
    SlangFunc slangFunc = funcMap[0];
    // ss << "\n";
    ss << NBSP2 << "globalInits = [\n";
    for (auto insn : slangFunc.spanStmts) {
      ss << NBSP4 << insn << ",\n";
    }
    ss << NBSP2 << "], # end globalInits.\n\n";
  }

  void dumpObjs(std::stringstream &ss) {
    dumpRecords(ss);
    dumpFunctions(ss);
  }

  void dumpRecords(std::stringstream &ss) {
    ss << NBSP2 << "allRecords = {\n";
    for (auto slangRecord : recordMap) {
      ss << NBSP4;
      ss << "\"" << slangRecord.second.name << "\":\n";
      ss << slangRecord.second.toString();
      ss << ",\n\n";
    }
    ss << NBSP2 << "}, # end allRecords dict\n\n";
  }

  void dumpFunctions(std::stringstream &ss) {
    ss << NBSP2 << "allFunctions = {\n";
    std::string prefix;
    for (auto slangFunc : funcMap) {
      if (slangFunc.second.fullName == K_00_GLBL_INIT_FUNC_NAME) {
        continue;
      }

      ss << NBSP4; // indent
      ss << "\"" << slangFunc.second.fullName << "\":\n";
      ss << NBSP6 << "constructs.Func(\n";

      // members
      ss << NBSP8 << "name = "
         << "\"" << slangFunc.second.fullName << "\",\n";
      ss << NBSP8 << "paramNames = [";
      prefix = "";
      for (std::string &paramName : slangFunc.second.paramNames) {
        ss << prefix << "\"" << paramName << "\"";
        if (prefix.size() == 0) {
          prefix = ", ";
        }
      }
      ss << "],\n";
      ss << NBSP8
         << "variadic = " << (slangFunc.second.variadic ? "True" : "False")
         << ",\n";

      ss << NBSP8 << "returnType = " << slangFunc.second.retType << ",\n";

      // member: basicBlocks
      ss << "\n";
      // ss << NBSP8 << "# Note: -1 is always start/entry BB. (REQUIRED)\n";
      // ss << NBSP8 << "# Note: 0 is always end/exit BB (REQUIRED)\n";
      ss << NBSP8 << "instrSeq = [\n";
      if (slangFunc.second.hasBody && slangFunc.second.spanStmts.size() == 0) {
        ss << NBSP12 << "instr.NopI(),\n";
      } else {
        for (auto insn : slangFunc.second.spanStmts) {
          ss << NBSP12 << insn << ",\n";
        }
      }
      ss << NBSP8 << "], # instrSeq end.\n";

      // close this function object
      ss << NBSP6 << "), # " << slangFunc.second.fullName << "() end. \n\n";
    }
    ss << NBSP2 << "}, # end allFunctions dict\n\n";
  } // dumpFunctions()

  void writeProtoToFile(const spir::BitTU &bittu, const std::string &filename) {
    std::ofstream output(filename, std::ios::binary);
    if (!output) {
      std::cerr << ENAME ": Failed to open " << filename << " for writing."
                << std::endl;
      return;
    }
    if (!bittu.SerializeToOstream(&output)) {
      std::cerr << ENAME ": Failed to write protobuf message to " << filename
                << std::endl;
    }
  }

  // BOUND END  : dump_routines (to SPAN Strings)

}; // class SlangTranslationUnit

class SpirGenerator {

private:
  // static_members initialized
  SlangTranslationUnit stu;
  FunctionDecl *FD; // The active function decl being processed
  ASTContext *Ctx;
  SmallVectorImpl<char> *charSv;
  BitFunc* currentBitFunc;

public:

  SpirGenerator(ASTContext *ctx) : Ctx(ctx) {
    stu.uniqLabelCounter = 0;
    stu.uniqIdCounter = 0;
    stu.isStaticLocal = false;
    stu.uniqRecordIdCounter = 0;
    stu.switchCfls = nullptr;

    FD = nullptr;
    charSv = new SmallVector<char, 64>();
    charSv->data()[0] = '\0';
  }

  // BOUND START: top_level_routines

  void slangInit(const TranslationUnitDecl *TU) {
    // Get the full path from source manager
    std::string fullPath = Ctx->getSourceManager().getFileEntryForID(
        Ctx->getSourceManager().getMainFileID())->tryGetRealPathName().str();

    // Extract the filename and directory from the full path
    size_t lastSlash = fullPath.find_last_of("/\\");
    stu.tuName = fullPath.substr(lastSlash + 1);
    stu.tuDirectory = fullPath.substr(0, lastSlash);
    
    // Store the translation unit name in the protobuf message
    stu.bittu.set_tuname(stu.tuName);
    stu.bittu.set_abspath(fullPath);

    // Add the origin and version of the TU
    stu.bittu.set_origin("Clang AST " + clang::getClangFullVersion());
  }

  // It is invoked once for each source translation unit function.
  void handleFunctionDecl(FunctionDecl *D) {
    SLANG_EVENT("BOUND START: SLANG_Generated_Output.\n")

    if (FD) {
      FD = FD->getCanonicalDecl();
      FD = const_cast<FunctionDecl*>(handleFuncNameAndType(FD, true));
      stu.currFunc = &stu.funcMap[(uint64_t) FD];
      SLANG_DEBUG("CurrentFunction: " << stu.currFunc->name << " " << (uint64_t)FD->getCanonicalDecl())
      if (FD->isVariadic()) {
        SLANG_ERROR("ERROR:VariadicFunction(SkippingBody): "\
          << stu.currFunc->name << " " << (uint64_t)FD->getCanonicalDecl())
      } else {
        handleFunctionBody(FD); // only for non-variadic functions.
      }
    } else {
      SLANG_ERROR("Decl is not a Function")
    }
  } // checkASTCodeBody()

  // invoked when the whole translation unit has been processed
  void checkEndOfTranslationUnit(const TranslationUnitDecl *TU) {
    stu.dumpSlangIr();
    SLANG_EVENT("Translation Unit Ended.\n")
    SLANG_EVENT("BOUND END  : SLANG_Generated_Output.\n")
  } // checkEndOfTranslationUnit()

  // BOUND END  : top_level_routines

  // BOUND START: handling_routines

  // All global initializations are put in a special function.
  void handleGlobalInits(const TranslationUnitDecl *decl) {
    if (!decl) {
      SLANG_FATAL("TranslationUnitDecl is null");
      return;
    }
  
    // Initialize the BitTU function for global inits
    BitFunc* bitFunc = stu.bittu.add_functions();
    bitFunc->set_fid(K_00_GLBL_INIT_FUNC_ID);
    bitFunc->set_fname(K_00_GLBL_INIT_FUNC_NAME);
    currentBitFunc = bitFunc; // mark the current function being processed

    SlangFunc slangFunc;
    slangFunc.fullName  = slangFunc.name = K_00_GLBL_INIT_FUNC_NAME;
    stu.funcMap[0]      = slangFunc;
    stu.currFunc        = &stu.funcMap[0];   // the special global function
  
    for (auto it = decl->decls_begin(); it != decl->decls_end(); ++it) {
      const VarDecl *varDecl = dyn_cast<VarDecl>(*it);
      if (varDecl) {
        SLANG_DEBUG("Found global variable: "
                    << varDecl->getNameAsString() << " at "
                    << getSrcLoc(varDecl).DebugString());
        handleVarDecl(varDecl);
      }
    }
  } // handleGlobalInits()

  void handleFunctionBody(FunctionDecl *funcDecl) {
    const Stmt *body = funcDecl->getBody();
    if (funcDecl->hasBody()) {
      stu.currFunc->hasBody = true;
      convertStmt(body);
      SLANG_DEBUG("FunctionHasBody: " << funcDecl->getNameAsString())
    } else {
      // FIXME: control doesn't reach here :(
      stu.currFunc->hasBody = false;
      SLANG_ERROR("No body for function: " << funcDecl->getNameAsString())
    }
  }

  // records the function details
  const FunctionDecl* handleFuncNameAndType(const FunctionDecl *funcDecl,
      bool force=false) {
    const FunctionDecl *realFuncDecl = funcDecl;

    if (funcDecl->isDefined()) {
      funcDecl = funcDecl->getDefinition();
      realFuncDecl = funcDecl;
      // funcDecl = funcDecl->getCanonicalDecl();
    }

    if (stu.funcMap.find((uint64_t)funcDecl) == stu.funcMap.end() || force) {
      // if here, function not already present. Add its details.

      SlangFunc slangFunc{};
      slangFunc.name = funcDecl->getNameInfo().getAsString();
      slangFunc.fullName = stu.convertFuncName(slangFunc.name);
      SLANG_DEBUG("AddingFunction: " << slangFunc.name << " " << (uint64_t)funcDecl\
      << " " << funcDecl->isDefined() << " " << (uint64_t)funcDecl->getCanonicalDecl())


      // STEP 1.2: Get function parameters.
      // if (funcDecl->doesThisDeclarationHaveABody())  //& !funcDecl->hasPrototype())
      for (unsigned i = 0, e = funcDecl->getNumParams(); i != e; ++i) {
        const ParmVarDecl *paramVarDecl = funcDecl->getParamDecl(i);
        handleValueDecl(paramVarDecl, slangFunc.name); // adds the var too
        slangFunc.paramNames.push_back(stu.getVar((uint64_t)paramVarDecl).name);
      }
      slangFunc.variadic = funcDecl->isVariadic();

      // STEP 1.3: Get function return type.
      slangFunc.retType = convertClangType(funcDecl->getReturnType());

      // STEP 2: Copy the function to the map.
      stu.funcMap[(uint64_t)funcDecl] = slangFunc;
    }

    return realFuncDecl;
  } // handleFuncNameAndType()

  // All variable declarations are handled here.
  void handleVarDecl(const VarDecl *varDecl, std::string funcName = "") {
    uint64_t varAddr = (uint64_t)varDecl;
    std::string varName;

    stu.isStaticLocal = varDecl->isStaticLocal();

    if (stu.isNewVar(varAddr)) {
      // Seeing the variable for the first time here.
      SlangVar slangVar{};
      slangVar.id = varAddr;

      varName = varDecl->getNameAsString();

      //delit slangVar.typeStr = convertClangType(varDecl->getType());

      // Create BitDataType for the variable and store in BitTU
      BitDataType *dt = new BitDataType();
      convertClangTypeBit(varDecl->getType(), dt);

      BitEntityInfo bitEntityInfo;
      bitEntityInfo.set_eid(varAddr);
      bitEntityInfo.set_allocated_dt(dt);

      SLANG_DEBUG("NEW_VAR: " << slangVar.convertToString())

      if (varName == "") {
        // used only to name anonymous function parameters
        varName = slang::Util::getNextUniqueIdStr() + "param";
      }

      if (varDecl->isStaticLocal()) {
        slangVar.setLocalVarNameStatic(varName, funcName);
        bitEntityInfo.set_ekind(EVAR_LOCL_STATIC);
      } else if (varDecl->hasLocalStorage()) {
        slangVar.setLocalVarName(varName, funcName);
        bitEntityInfo.set_ekind(EVAR_LOCL);
        if (stu.varCountMap.find(slangVar.name) != stu.varCountMap.end()) {
          stu.varCountMap[slangVar.name]++;
          uint64_t newVarId = stu.varCountMap[slangVar.name];
          slangVar.setLocalVarName(std::to_string(newVarId) + "D" + varName, funcName);
        } else {
          stu.varCountMap[slangVar.name] = 1;
        }
      } else if (varDecl->hasGlobalStorage()) {
        slangVar.setGlobalVarName(varName);
        bitEntityInfo.set_ekind(EVAR_GLBL);
      } else if (varDecl->hasExternalStorage()) {
        SLANG_ERROR("External Storage Not Handled.")
      } else {
        SLANG_ERROR("ERROR:Unknown variable storage.")
      }

      stu.addVar(slangVar.id, slangVar);
      bitEntityInfo.set_allocated_loc(getSrcLocBit(varDecl));
      bitEntityInfo.set_strval(slangVar.name);
      stu.bittu.mutable_entities()->emplace(slangVar.name, slangVar.id);
      stu.bittu.mutable_entityinfo()->emplace(slangVar.id, bitEntityInfo);
      return; //delit

      if (varDecl->getType()->isArrayType()) {
        auto arrayType = varDecl->getType()->getAsArrayTypeUnsafe();
        if (isa<VariableArrayType>(arrayType)) {
          SlangExpr varExpr = convertVariable(varDecl, getLocationString(varDecl));
          SlangExpr sizeExpr = convertVarArrayVariable(varDecl->getType(),
                                                       arrayType->getElementType());

          SlangExpr allocExpr;
          std::stringstream ss;
          ss << "expr.AllocE(" << sizeExpr.expr;
          ss << ", " << getLocationString(varDecl) << ")";
          allocExpr.expr = ss.str();
          allocExpr.qualType = Ctx->VoidPtrTy;
          allocExpr.locStr = getLocationString(varDecl);
          allocExpr.compound = true;

          SlangExpr tmpVoidPtr = convertToTmp(allocExpr);

          SlangExpr castExpr;
          ss.str("");
          ss << "expr.CastE(" << tmpVoidPtr.expr;
          ss << ", " << convertClangType(varDecl->getType());
          ss << ", " << getLocationString(varDecl) << ")";
          castExpr.expr = ss.str();
          castExpr.qualType = varDecl->getType();
          castExpr.compound = true;
          castExpr.locStr = getLocationString(varDecl);

          addAssignInstr(varExpr, castExpr, getLocationString(varDecl));

          BitEntity* varEntity = convertVariableBit(varDecl);
          BitEntity sizeEntity = convertVarArrayVariableBit(varDecl->getType(),
              arrayType->getElementType());
          
          BitExpr* allocExpr = createUnaryExprBit(sizeEntity, K_XK::XALLOC);
          BitEntity* tmpVoidPtr = convertToTmpBit(allocExpr);
          
          BitExpr* castExprBit = createUnaryExprBit(tmpVoidPtr, K_XK::CAST);

          addAssignInstrBit(convertEntityToExprBit(varEntity), castExprBit);
        }
      }

      // check if it has a initialization body
      if (varDecl->hasInit()) {
        // yes it has, so initialize it
        if (varDecl->getInit()->getStmtClass() == Stmt::InitListExprClass) {
          SLANG_ERROR("ERROR:AggregateInit: Check if the output is correct.")
          varDecl->dump();
          // std::vector<uint32_t> indexVector;
          // convertInitListExpr(slangVar, cast<InitListExpr>(varDecl->getInit()),
          //    varDecl, indexVector, varDecl->isStaticLocal());

          SlangExpr slangExpr = convertSlangVar(slangVar, varDecl);
          convertInitListExprNew(slangExpr, cast<InitListExpr>(varDecl->getInit()));
        } else {
          //if (varDecl->hasLocalStorage()) { // do it for global as well
          SlangExpr slangExpr = convertStmt(varDecl->getInit());
          if (slangExpr.expr == "ERROR:Unknown") {
            SLANG_ERROR("SEARCH_ME")
          }
          std::string locStr = getLocationString(varDecl);
          std::stringstream ss;
          ss << "instr.AssignI(";
          ss << "expr.VarE(\"" << slangVar.name << "\"";
          ss << ", " << locStr << ")"; // close expr.VarE(...
          ss << ", " << slangExpr.expr;
          ss << ", " << locStr << ")"; // close instr.AssignI(...
          if (varDecl->isStaticLocal()) { // them make a global init
            auto func = &stu.funcMap[0];
            func->spanStmts.push_back(ss.str());
          } else {
            stu.addStmt(ss.str());
          }
          // }
        }
      }
    } // if (stu.isNewVar(varAddr))

    // else: No need to re-process an already processed variable.

    stu.isStaticLocal = false;
  } // handleVarDecl()


  // record the variable name and type
  void handleValueDecl(const ValueDecl *valueDecl, std::string funcName) {
    const VarDecl *varDecl = dyn_cast<VarDecl>(valueDecl);

    std::string varName;
    if (varDecl) {
      handleVarDecl(varDecl, funcName);

    } else if(valueDecl->getAsFunction()) {
      handleFuncNameAndType(valueDecl->getAsFunction());

    } else {
      SLANG_ERROR("ValueDecl is not a VarDecl or a FunctionDecl!")
      SLANG_TRACE_GUARD(valueDecl->dump());
    }
  } // handleValueDecl()


  void handleDeclStmt(const DeclStmt *declStmt) {
    SLANG_DEBUG("Set last DeclStmt to DeclStmt at " << (uint64_t)(declStmt));

    std::stringstream ss;

    for (auto it = declStmt->decl_begin(); it != declStmt->decl_end(); ++it) {
      if (isa<VarDecl>(*it)) {
        handleVarDecl(cast<VarDecl>(*it), stu.currFunc->name);
      }
    }
  } // handleDeclStmt()

  // BOUND END  : handling_routines

  // BOUND START: conversion_routines

  // stmtconversion
  SlangExpr convertStmt(const Stmt *stmt) {
    SlangExpr slangExpr;

    if (!stmt) { return slangExpr; }

    SLANG_INFO("ConvertingStmt : " << stmt->getStmtClassName() << "\n")

    switch (stmt->getStmtClass()) {
    case Stmt::PredefinedExprClass:
      return convertPredefinedExpr(cast<PredefinedExpr>(stmt));

    case Stmt::StmtExprClass:
      return convertStmtExpr(cast<StmtExpr>(stmt));

    case Stmt::CaseStmtClass:
      return convertCaseStmt(cast<CaseStmt>(stmt));

    case Stmt::DefaultStmtClass:
      return convertDefaultCaseStmt(cast<DefaultStmt>(stmt));

    case Stmt::BreakStmtClass:
      return convertBreakStmt(cast<BreakStmt>(stmt));

    case Stmt::ContinueStmtClass:
      return convertContinueStmt(cast<ContinueStmt>(stmt));

    case Stmt::LabelStmtClass:
      return convertLabel(cast<LabelStmt>(stmt));

    case Stmt::ConditionalOperatorClass:
      return convertConditionalOp(cast<ConditionalOperator>(stmt));

    case Stmt::IfStmtClass:
      return convertIfStmt(cast<IfStmt>(stmt));

    case Stmt::WhileStmtClass:
      return convertWhileStmt(cast<WhileStmt>(stmt));

    case Stmt::DoStmtClass:
      return convertDoStmt(cast<DoStmt>(stmt));

    case Stmt::ForStmtClass:
      return convertForStmt(cast<ForStmt>(stmt));

    case Stmt::UnaryOperatorClass:
      return convertUnaryOperator(cast<UnaryOperator>(stmt));

    case Stmt::CompoundAssignOperatorClass:
    case Stmt::BinaryOperatorClass:
      return convertBinaryOperator(cast<BinaryOperator>(stmt));

    case Stmt::ParenExprClass:
      return convertParenExpr(cast<ParenExpr>(stmt));

    case Stmt::CompoundStmtClass:
      return convertCompoundStmt(cast<CompoundStmt>(stmt));

    case Stmt::DeclStmtClass:
      handleDeclStmt(cast<DeclStmt>(stmt)); break;

    case Stmt::DeclRefExprClass:
      return convertDeclRefExpr(cast<DeclRefExpr>(stmt));

    case Stmt::ConstantExprClass:
      return convertConstantExpr(cast<ConstantExpr>(stmt));

    case Stmt::IntegerLiteralClass:
      return convertIntegerLiteral(cast<IntegerLiteral>(stmt));

    case Stmt::CharacterLiteralClass:
      return convertCharacterLiteral(cast<CharacterLiteral>(stmt));

    case Stmt::FloatingLiteralClass:
      return convertFloatingLiteral(cast<FloatingLiteral>(stmt));

    case Stmt::StringLiteralClass:
      return convertStringLiteral(cast<StringLiteral>(stmt));

    case Stmt::ImplicitCastExprClass:
      return convertImplicitCastExpr(cast<ImplicitCastExpr>(stmt));

    case Stmt::ReturnStmtClass:
      return convertReturnStmt(cast<ReturnStmt>(stmt));

    case Stmt::SwitchStmtClass:
      return convertSwitchStmtNew(cast<SwitchStmt>(stmt));

    case Stmt::GotoStmtClass:
      return convertGotoStmt(cast<GotoStmt>(stmt));

    case Stmt::CStyleCastExprClass:
      return convertCStyleCastExpr(cast<CStyleCastExpr>(stmt));

    case Stmt::MemberExprClass:
      return convertMemberExpr(cast<MemberExpr>(stmt));

    case Stmt::ArraySubscriptExprClass:
      return convertArraySubscriptExpr(cast<ArraySubscriptExpr>(stmt));

    case Stmt::UnaryExprOrTypeTraitExprClass:
      return convertUnaryExprOrTypeTraitExpr(cast<UnaryExprOrTypeTraitExpr>(stmt));    

    case Stmt::CallExprClass:
      return convertCallExpr(cast<CallExpr>(stmt));

    // case Stmt::CaseStmtClass:
    //   // we manually handle case stmt when we handle switch stmt
    //   break;

    case Stmt::NullStmtClass: // just a ";"
      stu.addStmt("instr.NopI(" + getLocationString(stmt) + ")");
      break;

    default:
      SLANG_ERROR("ERROR:Unhandled_Stmt: " << stmt->getStmtClassName())
      stmt->dump();
      break;
    }

    slangExpr.expr = "ERROR:Unknown";
    return slangExpr;
  } // convertStmt()


  /*
   * As observer: PredefinedExpr has only a single child expression.
   * `-PredefinedExpr 0x563d8a43fdb8 <col:233> 'const char [23]' lvalue __PRETTY_FUNCTION__
   *   `-StringLiteral 0x563d8a43fd88 <col:233> 'const char [23]' lvalue "int main(int, char **)"
   */
  SlangExpr convertPredefinedExpr(const PredefinedExpr *pe) {
    auto it = pe->child_begin();
    return convertStmt(*it);
  }


  /*
   * StmtExpr - This is the GNU Statement Expression extension: ({int X=4; X;}).
   */
  SlangExpr convertStmtExpr(const StmtExpr *stmt) {
    SlangExpr expr;

    for (auto it=stmt->child_begin(); it != stmt->child_end(); ++it) {
      expr = convertStmt(*it);
    }

    return expr; // return the last expression
  }


  SlangExpr convertVarArrayVariable(QualType valueType, QualType elementType) {
    const Type *elemTypePtr = elementType.getTypePtr();
    const VariableArrayType *varArrayType =
        cast<VariableArrayType>(valueType.getTypePtr()->getAsArrayTypeUnsafe());

    if (elemTypePtr->isArrayType()) {
      // it will definitely be a VarArray Type (since this func is called)
      SlangExpr tmpSubArraySize = convertVarArrayVariable(elementType,
          elemTypePtr->getAsArrayTypeUnsafe()->getElementType());

      SlangExpr thisVarArrSizeExpr = convertToTmp(
          convertStmt(varArrayType->getSizeExpr()));

      SlangExpr sizeOfThisVarArrExpr = convertToTmp(createBinaryExpr(thisVarArrSizeExpr,
          "op.BO_MUL", tmpSubArraySize, thisVarArrSizeExpr.locStr,
          varArrayType->getSizeExpr()->getType()));

      SlangExpr tmpThisArraySize = convertToTmp(sizeOfThisVarArrExpr);
      return tmpThisArraySize;

    } else {
      // a non-array element type
      TypeInfo typeInfo = Ctx->getTypeInfo(elementType);
      uint64_t size = typeInfo.Width / 8;

      SlangExpr thisVarArrSizeExpr = convertToTmp(
          convertStmt(varArrayType->getSizeExpr()));

      SlangExpr sizeOfInnerNonVarArrType;
      std::stringstream ss;
      ss << "expr.LitE(" << size;
      ss << ", " << thisVarArrSizeExpr.locStr << ")";
      sizeOfInnerNonVarArrType.expr = ss.str();
      sizeOfInnerNonVarArrType.qualType = Ctx->UnsignedIntTy;
      sizeOfInnerNonVarArrType.locStr = thisVarArrSizeExpr.locStr;

      SlangExpr sizeOfThisVarArrExpr = convertToTmp(
          createBinaryExpr(thisVarArrSizeExpr,
              "op.BO_MUL", sizeOfInnerNonVarArrType, thisVarArrSizeExpr.locStr,
              sizeOfInnerNonVarArrType.qualType));

      SlangExpr tmpThisArraySize = convertToTmp(sizeOfThisVarArrExpr);
      return tmpThisArraySize;
    }
  } // convertVarArrayVariable()

  BitExpr convertVarArrayVariableBit(QualType valueType, QualType elementType) {
    const Type *elemTypePtr = elementType.getTypePtr();
    const VariableArrayType *varArrayType =
        cast<VariableArrayType>(valueType.getTypePtr()->getAsArrayTypeUnsafe());

    if (elemTypePtr->isArrayType()) {
      // it will definitely be a VarArray Type (since this func is called)
      SlangExpr tmpSubArraySize = convertVarArrayVariable(elementType,
          elemTypePtr->getAsArrayTypeUnsafe()->getElementType());

      SlangExpr thisVarArrSizeExpr = convertToTmp(
          convertStmt(varArrayType->getSizeExpr()));

      SlangExpr sizeOfThisVarArrExpr = convertToTmp(createBinaryExpr(thisVarArrSizeExpr,
          "op.BO_MUL", tmpSubArraySize, thisVarArrSizeExpr.locStr,
          varArrayType->getSizeExpr()->getType()));

      SlangExpr tmpThisArraySize = convertToTmp(sizeOfThisVarArrExpr);
      return tmpThisArraySize;

    } else {
      // a non-array element type
      TypeInfo typeInfo = Ctx->getTypeInfo(elementType);
      uint64_t size = typeInfo.Width / 8;

      SlangExpr thisVarArrSizeExpr = convertToTmp(
          convertStmt(varArrayType->getSizeExpr()));

      SlangExpr sizeOfInnerNonVarArrType;
      std::stringstream ss;
      ss << "expr.LitE(" << size;
      ss << ", " << thisVarArrSizeExpr.locStr << ")";
      sizeOfInnerNonVarArrType.expr = ss.str();
      sizeOfInnerNonVarArrType.qualType = Ctx->UnsignedIntTy;
      sizeOfInnerNonVarArrType.locStr = thisVarArrSizeExpr.locStr;

      SlangExpr sizeOfThisVarArrExpr = convertToTmp(
          createBinaryExpr(thisVarArrSizeExpr,
              "op.BO_MUL", sizeOfInnerNonVarArrType, thisVarArrSizeExpr.locStr,
              sizeOfInnerNonVarArrType.qualType));

      SlangExpr tmpThisArraySize = convertToTmp(sizeOfThisVarArrExpr);
      return tmpThisArraySize;
    }
  } // convertVarArrayVariableBit()

  SlangExpr convertInitListExprNew(
      SlangExpr& lhs, // SlangVar& slangVar,
      const InitListExpr *initListExpr
  ) {
    uint32_t index = 0;
    SLANG_DEBUG("INIT_LIST_EXPR_NEW dump:");
    initListExpr->dump();
    initListExpr->getType().dump();

    for (const auto *it = initListExpr->begin(); it != initListExpr->end(); ++it) {
      const Stmt *stmt = *it;
      // compute the lhs of the assignment
      SlangExpr currLhs = genInitLhsExprNew(lhs, initListExpr->getType(), index);

      if (stmt->getStmtClass() == Stmt::InitListExprClass) {
        // handle sub-init-list here
        auto subInitExpr = cast<InitListExpr>(stmt);
        SlangExpr subLhs = convertToTmp2(currLhs); //, subInitExpr->getType());
        convertInitListExprNew(subLhs, subInitExpr);
      } else  if (stmt->getStmtClass() == Stmt::ImplicitValueInitExprClass) {
          // handle sub-init-list here
          auto subInitExpr = cast<ImplicitValueInitExpr>(stmt);
          SlangExpr subLhs = convertToTmp2(currLhs); //, subInitExpr->getType());
          convertImplicitValueInitExpr(subLhs, subInitExpr);
      } else {
        // compute the rhs part
        SlangExpr rhs = convertToTmp(convertStmt(stmt));
        addAssignInstr(currLhs, rhs, getLocationString(stmt));
      }
      index += 1;
    }

    return SlangExpr{};
  } // convertInitListExprNew()


  SlangExpr convertImplicitValueInitExpr(
      SlangExpr& lhs, // SlangVar& slangVar,
      const ImplicitValueInitExpr *initListExpr
  ) {
    uint32_t index = 0;
    SLANG_DEBUG("INIT_LIST_EXPR_NEW dump:");
    initListExpr->dump();
    initListExpr->getType().dump();

    for (auto it = initListExpr->child_begin(); it != initListExpr->child_end(); ++it) {
      const Stmt *stmt = *it;
      // compute the lhs of the assignment
      SlangExpr currLhs = genInitLhsExprNew(lhs, initListExpr->getType(), index);

      if (stmt->getStmtClass() == Stmt::InitListExprClass) {
        // handle sub-init-list here
        auto subInitExpr = cast<InitListExpr>(stmt);
        SlangExpr subLhs = convertToTmp2(currLhs); //, subInitExpr->getType());
        convertInitListExprNew(subLhs, subInitExpr);
      } else  if (stmt->getStmtClass() == Stmt::ImplicitValueInitExprClass) {
        // handle sub-init-list here
        auto subInitExpr = cast<ImplicitValueInitExpr>(stmt);
        SlangExpr subLhs = convertToTmp2(currLhs); //, subInitExpr->getType());
        convertImplicitValueInitExpr(subLhs, subInitExpr);
      } else {
        // compute the rhs part
        SlangExpr rhs = convertToTmp(convertStmt(stmt));
        addAssignInstr(currLhs, rhs, getLocationString(stmt));
      }
      index += 1;
    }

    return SlangExpr{};
  } // convertImplicitCastExpr()


  SlangExpr convertInitListExpr(SlangVar& slangVar, const InitListExpr *initListExpr,
      const VarDecl *varDecl, std::vector<uint32_t>& indexVector, bool staticLocal) {
    uint32_t index = 0;
    SLANG_DEBUG("INIT_LIST_EXPR dump:");
    initListExpr->dump();
    initListExpr->getType().dump();
    for (auto it = initListExpr->begin(); it != initListExpr->end(); ++it) {
      const Stmt *stmt = *it;
      if (stmt->getStmtClass() == Stmt::InitListExprClass) {
          // && isCompoundTypeAt(varDecl, indexVector))
        indexVector.push_back(index);
        convertInitListExpr(slangVar, cast<InitListExpr>(stmt), varDecl, indexVector, staticLocal);
        indexVector.pop_back();
      } else {
        SlangExpr rhs = convertToTmp(convertStmt(stmt));

        indexVector.push_back(index);
        SlangExpr lhs = genInitLhsExpr(slangVar, varDecl, indexVector);
        indexVector.pop_back();

        addAssignInstr(lhs, rhs, getLocationString(stmt));
      }
      index += 1;
    }

    return SlangExpr{};
  } // convertInitListExpr()

  // checks if the
  bool isCompoundTypeAt(const VarDecl *varDecl,
      std::vector<int>& indexVector) {
    // TODO
    return true;
  }

  SlangExpr genInitLhsExprNew(
      SlangExpr& lhs, // SlangVar& slangVar,
      QualType initExprListQt,
      int index
  ) {
    SlangExpr slangExpr;
    std::stringstream ss;

    const auto *type = initExprListQt.getTypePtr();

    std::string prefix = "";
    if (type->isArrayType()) {
      ss << prefix << "expr.ArrayE(";
      ss << "expr.LitE(" << index << ", " << lhs.locStr << ")";
      ss << ", " << lhs.expr; // must be a variable expr only
      ss << ", " << lhs.locStr << ")"; // end expr.ArrayE(

      slangExpr.expr = ss.str();
      slangExpr.qualType = type->getAsArrayTypeUnsafe()->getElementType();
    } else {
      // must be a record type
      const RecordDecl *recordDecl;

      if (type->isStructureType()) {
        recordDecl = type->getAsStructureType()->getDecl();
      } else { // must be a union then
        recordDecl = type->getAsUnionType()->getDecl();
      }

      auto slangRecord = stu.getRecord((uint64_t)recordDecl);
      slangRecord.genMemberAccessExpr(lhs.expr, lhs.locStr, index, slangExpr);
    }

    slangExpr.compound = true;
    slangExpr.locStr = lhs.locStr;
    return slangExpr;
  } // genInitLhsExprNew()


  // used to generate lhs (lvalue) for initializer lists like
  // int arr[][2] = {{1, 2}, {3, 4}, {5, 6}}; // for each element
  // it also works for the struct types
  SlangExpr genInitLhsExpr(SlangVar& slangVar,
      const VarDecl *varDecl, std::vector<uint32_t>& indexVector) {
    SlangExpr slangExpr;
    std::stringstream ss;

    std::string prefix = "";
    if (varDecl->getType()->isArrayType()) {
      for (auto it = indexVector.end()-1; it != indexVector.begin()-1; --it) {
        ss << prefix << "expr.ArrayE(" << "expr.LitE(" << *it <<
          ", " << getLocationString(varDecl) << ")";
        if (prefix == "") {
          prefix = ", ";
        }
      }

      ss << ", expr.VarE(\"" << slangVar.name << "\"";
      ss << ", " << getLocationString(varDecl) << ")";

      for (auto it = indexVector.begin(); it != indexVector.end(); ++it) {
        ss << ", " << getLocationString(varDecl) << ")";
      }

      slangExpr.expr = ss.str();
      slangExpr.compound = true;
      slangExpr.qualType = varDecl->getType();
      slangExpr.locStr = getLocationString(varDecl);
    } else {
      // must be a record type
      auto type = varDecl->getType();
      const RecordDecl *recordDecl;

      if (type->isStructureType()) {
        recordDecl = type->getAsStructureType()->getDecl();
      } else {
        // must be a union then
        recordDecl = type->getAsUnionType()->getDecl();
      }

      std::string memberListStr =
          stu.getRecord((uint64_t)recordDecl).genMemberExpr(indexVector);

      ss << memberListStr;
      ss << ", expr.VarE(\"" << slangVar.name << "\"";
      ss << ", " << getLocationString(varDecl) << ")";

      for (auto it = indexVector.begin(); it != indexVector.end(); ++it) {
        ss << ", " << getLocationString(varDecl) << ")";
      }

      slangExpr.expr = ss.str();
      slangExpr.compound = true;
      slangExpr.qualType = varDecl->getType();
      slangExpr.locStr = getLocationString(varDecl);
    }

    return slangExpr;
  } // genInitLhsExpr()

  // guaranteed to be a comma operator
  SlangExpr convertBinaryCommaOp(const BinaryOperator *binOp) {
    auto it = binOp->child_begin();
    const Stmt *leftOprnd = *it;
    ++it;
    const Stmt *rightOprnd = *it;

    convertStmt(leftOprnd);

    SlangExpr rightExpr = convertToTmp(convertStmt(rightOprnd));

    return rightExpr;
  } // convertBinaryCommaOp()

  SlangExpr convertCallExpr(const CallExpr *callExpr) {
    SlangExpr slangExpr;

    auto it = callExpr->child_begin();

    const Stmt *callee = *it;
    SlangExpr calleeExpr = convertToTmp(convertStmt(callee));

    std::vector<const Stmt*> args;
    ++it; // skip the callee expression
    for (; it != callExpr->child_end(); ++it) {
      args.push_back(*it);
    }

    std::stringstream ss;
    ss << "expr.CallE(" << calleeExpr.expr;
    if (args.size()) {
      std::string prefix = "";
      ss << ", [";
      for (auto argIter = args.begin(); argIter != args.end(); ++argIter) {
        SlangExpr tmpExpr = convertToTmp(convertStmt(*argIter));
        ss << prefix << tmpExpr.expr;
        if (prefix == "") {
          prefix = ", ";
        }
      }
      ss << "]";
    } else {
      ss << ", " << "None";
    }

    ss << ", " << getLocationString(callExpr) <<  ")"; // close expr.CallE(...

    slangExpr.expr = ss.str();
    slangExpr.qualType = callExpr->getType();
    slangExpr.locStr = getLocationString(callExpr);
    slangExpr.compound = true;
    ss.str("");

    if (hasVoidReturnType(callExpr) || isTopLevel(callExpr)) {
      ss << "instr.CallI(" << slangExpr.expr << ", " << slangExpr.locStr << ")";
      stu.addStmt(ss.str());
      return SlangExpr{}; // return empty expression
    }

    return slangExpr;
  }

  bool hasVoidReturnType(const CallExpr *callExpr) {
    QualType qt = callExpr->getType();
      if (qt.isNull()) {
        return true;
      }

      qt = getCleanedQualType(qt);
      const Type *type = qt.getTypePtr();
      return type->isVoidType();
  } // hasVoidReturnType()

  SlangExpr convertArraySubscriptExpr(const ArraySubscriptExpr *arrayExpr) {
    SlangExpr slangExpr;
    std::stringstream ss;

    auto it = arrayExpr->child_begin();
    const Stmt *object = *it;
    ++it;
    const Stmt *index = *it;

    SlangExpr parentExpr = convertToTmp(convertStmt(object));
    SlangExpr indexExpr = convertToTmp(convertStmt(index));
    SlangExpr tmpExpr;

    tmpExpr = parentExpr;

    ss.str("");
    ss << "expr.ArrayE(" << indexExpr.expr;
    ss << ", " << tmpExpr.expr;
    ss << ", " << getLocationString(arrayExpr) << ")";

    slangExpr.expr = ss.str();
    slangExpr.qualType = arrayExpr->getType();
    slangExpr.locStr = getLocationString(arrayExpr);
    slangExpr.compound = true;

    return slangExpr;
  } // convertArraySubscript()

  SlangExpr convertMemberExpr(const MemberExpr *memberExpr) {
    auto it = memberExpr->child_begin();
    const Stmt *child = *it;
    SlangExpr parentExpr = convertStmt(child);
    SlangExpr parentTmpExpr;
    SlangExpr memSlangExpr;
    std::stringstream ss;

    // store parent to a temporary
    parentTmpExpr = parentExpr;
    if (parentExpr.compound) {
      if (parentExpr.qualType.getTypePtr()->isPointerType()) {
          //|| !(parentExpr.expr.substr(0,12) == "expr.MemberE")) 
        parentTmpExpr = convertToTmp(parentExpr);
      } else {
        SlangExpr addrOfExpr;
        ss << "expr.AddrOfE(" << parentExpr.expr;
        ss << ", " << getLocationString(memberExpr) << ")";

        addrOfExpr.expr = ss.str();
        addrOfExpr.qualType = Ctx->getPointerType(parentExpr.qualType);
        addrOfExpr.locStr = getLocationString(memberExpr);
        addrOfExpr.compound = true;

        parentTmpExpr = convertToTmp(addrOfExpr);
      }
    }

    std::string memberName;
    memberName = memberExpr->getMemberNameInfo().getAsString();
    if (memberName == "") {
      memberName = stu.getVar((uint64_t)(memberExpr->getMemberDecl())).name;
    }

    ss.str("");
    ss << "expr.MemberE(\"" << memberName << "\"";
    ss << ", " << parentTmpExpr.expr;
    ss << ", " << getLocationString(memberExpr) << ")";

    memSlangExpr.expr = ss.str();
    memSlangExpr.qualType = memberExpr->getType();
    memSlangExpr.locStr = getLocationString(memberExpr);
    memSlangExpr.compound = true;

    SLANG_DEBUG("Array_Member_Expr: mem: " << memSlangExpr.expr);
    return memSlangExpr;
  } // convertMemberExpr()

  SlangExpr convertCStyleCastExpr(const CStyleCastExpr *cCast) {
    auto it = cCast->child_begin();
    QualType qt = cCast->getType();

    return convertCastExpr(*it, qt, getLocationString(cCast));
  } // convertCStyleCastExpr()

  SlangExpr convertGotoStmt(const GotoStmt *gotoStmt) {
    std::string label = gotoStmt->getLabel()->getNameAsString();
    addGotoInstr(label);
    return SlangExpr{};
  } // convertGotoStmt()

  SlangExpr convertBreakStmt(const BreakStmt *breakStmt) {
    addGotoInstr(stu.peekExitLabel());
    return SlangExpr{};
  }

  SlangExpr convertContinueStmt(const ContinueStmt *continueStmt) {
    addGotoInstr(stu.peekEntryLabel());
    return SlangExpr{};
  }

SlangExpr convertSwitchStmtNew(const SwitchStmt *switchStmt) {
    auto oldSwitchCfls = stu.switchCfls;
    auto switchCfls = SwitchCtrlFlowLabels(stu.genNextLabelCountStr());
    stu.switchCfls = &switchCfls;

    stu.pushLabels(stu.switchCfls->switchStartLabel, stu.switchCfls->switchExitLabel);

    addLabelInstr(stu.switchCfls->switchStartLabel);

    const Expr *condExpr = switchStmt->getCond();
    SlangExpr switchCond = convertToTmp(convertStmt(condExpr));
    stu.switchCfls->switchCond = switchCond;

    // Get all case statements inside switch.
    if (switchStmt->getBody()) {
        convertStmt(switchStmt->getBody());
    } else {
        for (auto it = switchStmt->child_begin(); it != switchStmt->child_end(); ++it) {
            convertStmt(*it);
        }
    }

    addGotoInstr(stu.switchCfls->nextBodyLabel);
    addLabelInstr(stu.switchCfls->nextCaseCondLabel); // the last condition label
    if (stu.switchCfls->defaultExists) {
        addGotoInstr(stu.switchCfls->defaultCaseLabel);
    }
    addLabelInstr(stu.switchCfls->nextBodyLabel);
    addLabelInstr(stu.switchCfls->switchExitLabel);
    stu.switchCfls = oldSwitchCfls;  // restore the old ptr

    stu.popLabel();
    return SlangExpr{};
} // convertSwitchStmtNew()


SlangExpr convertCaseStmt(const CaseStmt *caseStmt) {
    if (stu.switchCfls->thisCaseCondLabel != "") {
      addGotoInstr(stu.switchCfls->nextBodyLabel); // add a fall through for prev body
    }

    stu.switchCfls->setupForThisCase();

  const Stmt *cond = *(caseStmt->child_begin());
  SlangExpr caseCond = convertToTmp(convertStmt(cond));

  addLabelInstr(stu.switchCfls->thisCaseCondLabel); // condition label
  // add the actual condition
  SlangExpr eqExpr = convertToIfTmp(createBinaryExpr(
      stu.switchCfls->switchCond, "op.BO_EQ", caseCond,
      getLocationString(caseStmt), Ctx->UnsignedIntTy));
  addCondInstr(eqExpr.expr, stu.switchCfls->thisBodyLabel,
      stu.switchCfls->nextCaseCondLabel, getLocationString(caseStmt));

  // case body
  if (stu.switchCfls->gotoLabel != "") {
    std::stringstream ss;
    ss << "instr.LabelI(\"" << stu.switchCfls->gotoLabel << "\"";
    ss << ", " << stu.switchCfls->gotoLabelLocStr << ")"; // close instr.LabelI(...
    stu.addStmt(ss.str());
    stu.switchCfls->gotoLabel = stu.switchCfls->gotoLabelLocStr = "";
  }
  addLabelInstr(stu.switchCfls->thisBodyLabel);
  for (auto it = caseStmt->child_begin(); it != caseStmt->child_end(); ++it) {
    convertStmt(*it);
  }

  return SlangExpr{};
}

    SlangExpr convertDefaultCaseStmt(const DefaultStmt *defaultStmt) {
      if (stu.switchCfls->thisCaseCondLabel != "") {
        addGotoInstr(stu.switchCfls->nextBodyLabel); // add a fall through for prev body
      }

      stu.switchCfls->setupForDefaultCase();

      addLabelInstr(stu.switchCfls->defaultCaseLabel); // default case label

      // default body
      addLabelInstr(stu.switchCfls->thisBodyLabel); // body label
      for (auto it = defaultStmt->child_begin(); it != defaultStmt->child_end(); ++it) {
        convertStmt(*it);
      }

      return SlangExpr{};
    }

  SlangExpr convertSwitchStmt(const SwitchStmt *switchStmt) {
    std::string id = stu.genNextLabelCountStr();
    std::string switchStartLabel = id + "SwitchStart";
    std::string switchExitLabel = id + "SwitchExit";
    std::string caseCondLabel = id + "CaseCond" + "-";
    std::string caseBodyLabel = id + "CaseBody" + "-";
    std::string defaultLabel = id + "Default";
    bool defaultLabelAdded = false;

    stu.pushLabels(switchStartLabel, switchExitLabel);

    addLabelInstr(switchStartLabel);

    std::vector<const Stmt*> caseStmtsWithDefault;
    // std::vector<const Stmt*> defaultStmt;

    const Expr *condExpr = switchStmt->getCond();
    SlangExpr switchCond = convertToTmp(convertStmt(condExpr));

    // Get all case statements inside switch.
    if (switchStmt->getBody()) {
      getCaseStmts(caseStmtsWithDefault, switchStmt->getBody());
      // getDefaultStmt(defaultStmt, switchStmt->getBody());

    } else {
      for (auto it = switchStmt->child_begin(); it != switchStmt->child_end(); ++it) {
        if (isa<CaseStmt>(*it)) {
          getCaseStmts(caseStmtsWithDefault, (*it));
          // getDefaultStmt(defaultStmt, (*it));
        }
      }
    }

    std::stringstream ss;
    std::string label;
    std::string nextLabel;
    size_t totalStmts = caseStmtsWithDefault.size();
    for (size_t index=0; index < caseStmtsWithDefault.size(); ++index) {
      // for (const Stmt *stmt: caseStmtsWithDefault) {
      const Stmt *stmt = caseStmtsWithDefault[index];

      if (isa<CaseStmt>(stmt)) {
        const CaseStmt *caseStmt = cast<CaseStmt>(stmt);
        // find where to jump to if the case condition is false
        std::string falseLabel;
        falseLabel = defaultLabel;

        if (index != totalStmts - 1) {
          // try jumping to the next case's cond
          for (size_t i=index+1; i < totalStmts; ++i) {
            if (isa<CaseStmt>(caseStmtsWithDefault[i])) {
              ss << caseCondLabel << i;
              falseLabel = ss.str();
              ss.str("");
              break;
            }
          }
        }

        // armed with the falseLabel add the condition
        ss << caseCondLabel << index;
        std::string condLabel = ss.str();
        ss.str("");

        const Stmt *cond = *(caseStmt->child_begin());
        // llvm::errs() << "CASE-CASE-CASE\n"; cond->dump();
        SlangExpr caseCond = convertToTmp(convertStmt(cond));

        // generate body label
        ss << caseBodyLabel << index;
        std::string bodyLabel = ss.str();
        ss.str("");

        addLabelInstr(condLabel); // condition label
        // add the actual condition
        SlangExpr eqExpr = convertToIfTmp(createBinaryExpr(switchCond,
            "op.BO_EQ", caseCond, getLocationString(caseStmt),
            Ctx->UnsignedIntTy));
        addCondInstr(eqExpr.expr, bodyLabel, falseLabel, getLocationString(caseStmt));

        // case body
        addLabelInstr(bodyLabel);
        for (auto it = caseStmt->child_begin();
             it != caseStmt->child_end();
             ++it) {
          convertStmt(*it);
        }

        // if it has break, then jump to exit
        // Note: a break as child stmt is covered recursively
        if (caseOrDefaultStmtHasSiblingBreak(caseStmt)) {
          addGotoInstr(switchExitLabel);
        } else {
          // try jumping to the next case's body if present :)
          if (index != totalStmts-1) {
            if (isa<CaseStmt>(caseStmtsWithDefault[index + 1])) {
              ss << caseBodyLabel << index + 1;
              addGotoInstr(ss.str());
              ss.str("");
            } else {
              // must be default then, hence fall through to it
            }
          }
        }

      } else if (isa<DefaultStmt>(stmt)) {
        // add the default case
        addLabelInstr(defaultLabel);
        defaultLabelAdded = true;
        for (auto it = stmt->child_begin(); it != stmt->child_end();
             ++it) {
          convertStmt(*it);
        }

        // if it has break, then jump to exit
        // Note: a break as child stmt is covered recursively
        if (caseOrDefaultStmtHasSiblingBreak(stmt)) {
          addGotoInstr(switchExitLabel);
        } else {
          // try jumping to the next case's body
          if (index != totalStmts-1) {
            // must be a case stmt, since this is a default stmt :)
            ss << caseBodyLabel << index+1;
            addGotoInstr(ss.str());
            ss.str("");
          }
        }
      }

    }

    if (!defaultLabelAdded) {
      addLabelInstr(defaultLabel); // needed
    }
    addLabelInstr(switchExitLabel);

    stu.popLabel();
    return SlangExpr{};
  } // convertSwitchStmt()

  // many times BreakStmt is a sibling of CaseStmt/DefaultStmt
  // this function detects that
  bool caseOrDefaultStmtHasSiblingBreak(const Stmt *stmt) {
    const auto &parents = Ctx->getParents(DynTypedNode::create(*stmt));

    const Stmt *parentStmt = parents[0].get<Stmt>();
    bool lastStmtWasTheGivenCaseOrDefaultStmt = false;
    bool hasBreak = false;

    for (auto it = parentStmt->child_begin();
          it != parentStmt->child_end();
          ++it) {
      if (! *it) { continue; }

      if (isa<BreakStmt>(*it)) {
        if (lastStmtWasTheGivenCaseOrDefaultStmt) {
          hasBreak = true;
        }
        break;
      }

      if (lastStmtWasTheGivenCaseOrDefaultStmt) {
        lastStmtWasTheGivenCaseOrDefaultStmt = false;
      }
      if ((*it) == stmt) {
        lastStmtWasTheGivenCaseOrDefaultStmt = true;
      }
    }

    return hasBreak;
  } // caseOrDefaultStmtHasSiblingBreak()

  // Returns true if the type is not complete enough to give away a constant size
  bool isIncompleteType(const Type *type) {
      bool retVal = false;

      if (type->isIncompleteArrayType() || type->isVariableArrayType()) {
          retVal = true;
      }
      return retVal;
  }

  // get all case statements recursively (case stmts can be hierarchical)
  void getCaseStmts(std::vector<const Stmt*>& caseStmtsWithDefault, const Stmt *stmt) {
    if (! stmt) return;

    if (isa<CaseStmt>(stmt)) {
      auto caseStmt = cast<CaseStmt>(stmt);
      caseStmtsWithDefault.push_back(stmt);
      for (auto it = caseStmt->child_begin(); it != caseStmt->child_end(); ++it) {
        if ((*it) && isa<CaseStmt>(*it)) {
          getCaseStmts(caseStmtsWithDefault, (*it));
        }
      }

    } else if (isa<CompoundStmt>(stmt)) {
      const CompoundStmt *compoundStmt = cast<CompoundStmt>(stmt);
      for (auto it = compoundStmt->body_begin(); it != compoundStmt->body_end(); ++it) {
        getCaseStmts(caseStmtsWithDefault, (*it));
      }
    } else if (isa<SwitchStmt>(stmt)) {
      // do nothing, as it will be handled separately

    } else if (isa<DefaultStmt>(stmt)) {
      auto defaultStmt = cast<DefaultStmt>(stmt);
      caseStmtsWithDefault.push_back(stmt);
      for (auto it = defaultStmt->child_begin(); it != defaultStmt->child_end(); ++it) {
        if ((*it) && isa<CaseStmt>(*it)) {
          getCaseStmts(caseStmtsWithDefault, (*it));
        }
      }

    } else {
      if (stmt->child_begin() != stmt->child_end()) {
        for (auto it = stmt->child_begin(); it != stmt->child_end(); ++it) {
          getCaseStmts(caseStmtsWithDefault, (*it));
        }
      }
    }
  }

  // get the default stmt if present
  void getDefaultStmt(std::vector<const Stmt*>& defaultStmt, const Stmt *stmt) {
    if (! stmt) return;

    if (isa<DefaultStmt>(stmt)) {
      defaultStmt.push_back(stmt);

    } else if (isa<CaseStmt>(stmt)) {
      auto caseStmt = cast<CaseStmt>(stmt);
      for (auto it = caseStmt->child_begin(); it != caseStmt->child_end(); ++it) {
        if ((*it) && isa<CaseStmt>(*it)) {
          getDefaultStmt(defaultStmt, (*it));
        }
      }

    } else if (isa<CompoundStmt>(stmt)) {
      const CompoundStmt *compoundStmt = cast<CompoundStmt>(stmt);
      for (auto it = compoundStmt->body_begin(); it != compoundStmt->body_end(); ++it) {
        getDefaultStmt(defaultStmt, (*it));
      }
    } else if (isa<SwitchStmt>(stmt)) {
      // do nothing, as it will be handled separately
    } else {
      if (stmt->child_begin() != stmt->child_end()) {
        for (auto it = stmt->child_begin(); it != stmt->child_end(); ++it) {
          getDefaultStmt(defaultStmt, (*it));
        }
      }
    }
  }

  SlangExpr convertReturnStmt(const ReturnStmt *returnStmt) {
    const Expr *retVal = returnStmt->getRetValue();

    SlangExpr retExpr = convertToTmp(convertStmt(retVal));

    std::stringstream ss;
    if (retExpr.expr.size() == 0) {
      retExpr.expr = "None";
    }
    ss << "instr.ReturnI(" << retExpr.expr;
    ss << ", " << getLocationString(returnStmt) << ")";
    stu.addStmt(ss.str());

    return SlangExpr{};
  }

  SlangExpr convertConditionalOp(const ConditionalOperator *condOp) {
    const Expr *condition = condOp->getCond();

    SlangExpr cond = convertToTmp(convertStmt(condition));
    SlangExpr trueExpr = convertToTmp(convertStmt(condOp->getTrueExpr()));
    SlangExpr falseExpr = convertToTmp(convertStmt(condOp->getFalseExpr()));

    SlangExpr slangExpr;
    std::stringstream ss;
    ss << "expr.SelectE(" << cond.expr;
    ss << ", " << trueExpr.expr;
    ss << ", " << falseExpr.expr;
    ss << ", " << getLocationString(condition) << ")";
    slangExpr.expr = ss.str();
    slangExpr.compound = true;
    slangExpr.qualType = condOp->getType();

    return slangExpr;
  } // convertConditionalOp()

  SlangExpr convertIfStmt(const IfStmt *ifStmt) {
    std::string id = stu.genNextLabelCountStr();
    std::string ifTrueLabel = id + "IfTrue";
    std::string ifFalseLabel = id + "IfFalse";
    std::string ifExitLabel = id + "IfExit";

    const Stmt *condition = ifStmt->getCond();
    SlangExpr conditionExpr = convertStmt(condition);
    conditionExpr = convertToIfTmp(conditionExpr);

    addCondInstr(conditionExpr.expr,
        ifTrueLabel, ifFalseLabel, getLocationString(ifStmt));

    addLabelInstr(ifTrueLabel);

    const Stmt *body = ifStmt->getThen();
    if (body) { convertStmt(body); }

    addGotoInstr(ifExitLabel);
    addLabelInstr(ifFalseLabel);

    const Stmt *elseBody = ifStmt->getElse();
    if (elseBody) {
      convertStmt(elseBody);
    }

    addLabelInstr(ifExitLabel);

    return SlangExpr{}; // return empty expression
  } // convertIfStmt()

  SlangExpr convertWhileStmt(const WhileStmt *whileStmt) {
    std::string id = stu.genNextLabelCountStr();
    std::string whileCondLabel = id + "WhileCond";
    std::string whileBodyLabel = id + "WhileBody";
    std::string whileExitLabel = id + "WhileExit";

    stu.pushLabels(whileCondLabel, whileExitLabel);

    addLabelInstr(whileCondLabel);

    const Stmt *condition = whileStmt->getCond();
    SlangExpr conditionExpr = convertStmt(condition);
    conditionExpr = convertToIfTmp(conditionExpr);

    addCondInstr(conditionExpr.expr,
        whileBodyLabel, whileExitLabel, getLocationString(condition));

    addLabelInstr(whileBodyLabel);

    const Stmt *body = whileStmt->getBody();
    if (body) { convertStmt(body); }

    // unconditional jump to startConditionLabel
    addGotoInstr(whileCondLabel);

    addLabelInstr(whileExitLabel);

    stu.popLabel();
    return SlangExpr{}; // return empty expression
  } // convertWhileStmt()

  SlangExpr convertDoStmt(const DoStmt *doStmt) {
    std::string id = stu.genNextLabelCountStr();
    std::string doEntry = "DoEntry" + id;
    std::string doCond = "DoCond" + id;
    std::string doExit = "DoExit" + id;

    stu.pushLabels(doCond, doExit);

    // do body
    addLabelInstr(doEntry);
    const Stmt *body = doStmt->getBody();
    if (body) { convertStmt(body); }

    // while condition
    addLabelInstr(doCond);
    const Stmt *condition = doStmt->getCond();
    SlangExpr conditionExpr = convertToIfTmp(convertStmt(condition));
    addCondInstr(conditionExpr.expr,
        doEntry, doExit, getLocationString(condition));

    addLabelInstr(doExit);

    stu.popLabel();
    return SlangExpr{}; // return empty expression
  } // convertDoStmt()

  SlangExpr convertForStmt(const ForStmt *forStmt) {
    std::string id = stu.genNextLabelCountStr();
    std::string forCondLabel = id + "ForCond";
    std::string forBodyLabel = id + "ForBody";
    std::string forExitLabel = id + "ForExit";

    stu.pushLabels(forCondLabel, forExitLabel);

    // for init
    const Stmt *init = forStmt->getInit();
    if (init) { convertStmt(init); }

    // for condition
    const Stmt *condition = forStmt->getCond();

    addLabelInstr(forCondLabel);

    if (condition) {
      SlangExpr conditionExpr = convertToIfTmp(convertStmt(condition));

      addCondInstr(conditionExpr.expr,
          forBodyLabel, forExitLabel, getLocationString(condition));
    } else {
      addCondInstr("expr.LitE(1)",
                   forBodyLabel, forExitLabel, getLocationString(forStmt));
    }

    // for body
    addLabelInstr(forBodyLabel);

    const Stmt *body = forStmt->getBody();
    if (body) { convertStmt(body); }

    const Stmt *inc = forStmt->getInc();
    if (inc) { convertStmt(inc); }

    addGotoInstr(forCondLabel); // jump to for cond
    addLabelInstr(forExitLabel); // for exit

    stu.popLabel();
    return SlangExpr{}; // return empty expression
  } // convertForStmt()

  SlangExpr convertCastExpr(const Stmt *expr, QualType qt, std::string locStr) {
    // Generates CastE() expression.
    SlangExpr castExpr;
    SlangExpr exprArg = convertToTmp(convertStmt(expr));
    auto typePtr = qt.getTypePtr();
    if (typePtr->isVoidType()) {
      // A VOID cast shouldn't be used anywhere.
      castExpr.expr = "ERROR:Unkown VOID Cast";
      return castExpr; // return an empty expression
    }
    std::string castTypeStr = convertClangType(qt);

    std::stringstream ss;
    ss << "expr.CastE(" << exprArg.expr;
    ss << ", " << castTypeStr;
    ss << ", " << locStr << ")";

    castExpr.expr = ss.str();
    castExpr.compound = true;
    castExpr.qualType = qt;
    castExpr.locStr = locStr;

    return castExpr;
  } // convertCastExpr()

  SlangExpr convertImplicitCastExpr(const ImplicitCastExpr *iCast) {
    // only one child is expected
    auto it = iCast->child_begin();
    auto ck = iCast->getCastKind();

    switch(ck) {
      case CastKind::CK_IntegralToFloating:
      case CastKind::CK_FloatingToIntegral:
      case CastKind::CK_IntegralCast:
      case CastKind::CK_ArrayToPointerDecay: {
        return convertStmt(*it);
      }

      default:
        return convertStmt(*it);
        //return convertCastExpr(*it, iCast->getType(), getLocationString(iCast));
    }
  }

  SlangExpr convertCharacterLiteral(const CharacterLiteral *cl) {
    std::stringstream ss;
    ss << "expr.LitE(" << cl->getValue();
    ss << ", " << getLocationString(cl) << ")";

    SlangExpr slangExpr;
    slangExpr.expr = ss.str();
    slangExpr.locStr = getLocationString(cl);
    slangExpr.qualType = cl->getType();

    return slangExpr;
  } // convertCharacterLiteral()

  SlangExpr convertConstantExpr(const ConstantExpr *constExpr) {
    // a ConstantExpr contains a literal expression
    return convertStmt(constExpr->getSubExpr());
  } // convertConstantExpr()

  SlangExpr convertIntegerLiteral(const IntegerLiteral *il) {
    std::stringstream ss;
    std::string suffix = ""; // helps make int appear float

    std::string locStr = getLocationString(il);

    // check if int is implicitly casted to floating
    const auto &parents = Ctx->getParents(*il);
    if (!parents.empty()) {
      const Stmt *stmt1 = parents[0].get<Stmt>();
      if (stmt1) {
        switch (stmt1->getStmtClass()) {
        default:
          break;
        case Stmt::ImplicitCastExprClass: {
          const ImplicitCastExpr *ice = cast<ImplicitCastExpr>(stmt1);
          switch (ice->getCastKind()) {
          default:
            break;
          case CastKind::CK_IntegralToFloating:
            suffix = ".0";
            break;
          }
        }
        }
      }
    }

    bool is_signed = il->getType()->isSignedIntegerType();
    ss << "expr.LitE(";
    charSv->clear(); il->getValue().toString(*charSv, 10, is_signed);
    ss << charSv->data();
    //il->print(ss, is_signed);// << il->getValue().toString(10, is_signed);
    ss << suffix;
    ss << ", " << locStr << ")";
    SLANG_TRACE(ss.str())

    SlangExpr slangExpr;
    slangExpr.expr = ss.str();
    slangExpr.qualType = il->getType();
    slangExpr.locStr = getLocationString(il);

    return slangExpr;
  } // convertIntegerLiteral()

  SlangExpr convertFloatingLiteral(const FloatingLiteral *fl) {
    std::stringstream ss;
    bool toInt = false;

    std::string locStr = getLocationString(fl);

    // check if float is implicitly casted to int
    const auto &parents = Ctx->getParents(*fl);
    if (!parents.empty()) {
      const Stmt *stmt1 = parents[0].get<Stmt>();
      if (stmt1) {
        switch (stmt1->getStmtClass()) {
        default:
          break;
        case Stmt::ImplicitCastExprClass: {
          const ImplicitCastExpr *ice = cast<ImplicitCastExpr>(stmt1);
          switch (ice->getCastKind()) {
          default:
            break;
          case CastKind::CK_FloatingToIntegral:
            toInt = true;
            break;
          }
        }
        }
      }
    }

    ss << "expr.LitE(";
    if (toInt) {
      // ss << (int64_t)fl->getValue().convertToDouble();
      ss << (int64_t)fl->getValueAsApproximateDouble();
    } else {
      ss << std::fixed << fl->getValueAsApproximateDouble();
    }
    ss << ", " << locStr << ")";
    SLANG_TRACE(ss.str())

    SlangExpr slangExpr;
    slangExpr.expr = ss.str();
    slangExpr.qualType = fl->getType();
    slangExpr.locStr = getLocationString(fl);

    return slangExpr;
  } // convertFloatingLiteral()

  SlangExpr convertStringLiteral(const StringLiteral *sl) {
    SlangExpr slangExpr;
    std::stringstream ss;

    std::string locStr = getLocationString(sl);

    // with extra text at the end since """" could occur
    // making the string invalid in python
    ss << "expr.LitE(\"\"\"" << sl->getBytes().str() << "XXX\"\"\"";
    ss << ", " << locStr << ")";
    slangExpr.expr = ss.str();
    slangExpr.locStr = locStr;

    return slangExpr;
  } // convertStringLiteral()

  SlangExpr convertVariable(const VarDecl *varDecl,
      std::string locStr = "Info(Loc(33333,33333))") {
    std::stringstream ss;
    SlangExpr slangExpr;

    ss << "expr.VarE(\"" << stu.convertVarExpr((uint64_t)varDecl) << "\"";
    ss << ", " << locStr << ")";
    slangExpr.expr = ss.str();
    slangExpr.qualType = varDecl->getType();
    slangExpr.varId = (uint64_t)varDecl;
    slangExpr.locStr = getLocationString(varDecl);

    return slangExpr;
  } // convertVariable()

  BitEntity* convertVariableBit(const VarDecl *varDecl) {
    BitEntity be = new BitEntity();
    be->set_eid((uint64_t)varDecl);
    be->set_allocated_loc(getSrcLocBit(varDecl));
    return be;
  } // convertVariableBit()

  BitExpr* convertEntityToExprBit(BitEntity* be) {
    BitExpr* expr = new BitExpr();
    expr->set_xkind(K_XK::VAL);
    expr->set_allocated_opr1(be);
    expr->set_allocated_loc(new BitSrcLoc(be->loc()));
    return expr;
  } // convertEntityToExpr()


  SlangExpr convertSlangVar(
      SlangVar& slangVar,
      const VarDecl *varDecl
  ) {
    std::stringstream ss;
    SlangExpr slangExpr;

    ss << "expr.VarE(\"" << slangVar.name << "\"";
    ss << ", " << getLocationString(varDecl) << ")";

    slangExpr.expr = ss.str();
    slangExpr.qualType = varDecl->getType();
    slangExpr.varId = (uint64_t)varDecl;
    slangExpr.locStr = getLocationString(varDecl);

    return slangExpr;
  } // convertSlangVar()

  SlangExpr convertEnumConst(const EnumConstantDecl *ecd, std::string &locStr) {
    SlangExpr slangExpr;

    std::stringstream ss;
    auto value = ecd->getInitVal();
    charSv->clear(); value.toString(*charSv, 10, value.isSigned());
    ss << "expr.LitE(" << charSv->data();
    ss << ", " << locStr << ")";

    slangExpr.expr = ss.str();
    slangExpr.locStr = locStr;
    slangExpr.qualType = ecd->getType();

    return slangExpr;
  }

  SlangExpr convertDeclRefExpr(const DeclRefExpr *dre) {
    SlangExpr slangExpr;
    std::stringstream ss;

    std::string locStr = getLocationString(dre);

    const ValueDecl *valueDecl = dre->getDecl();
    if (isa<EnumConstantDecl>(valueDecl)) {
      auto ecd = cast<EnumConstantDecl>(valueDecl);
      return convertEnumConst(ecd, locStr);
    }

    // it may be a VarDecl or FunctionDecl
    handleValueDecl(valueDecl, stu.currFunc->name);

    if (isa<VarDecl>(valueDecl)) {
      auto varDecl = cast<VarDecl>(valueDecl);
      slangExpr = convertVariable(varDecl, getLocationString(dre));
      slangExpr.locStr = getLocationString(dre);
      return slangExpr;

    } else if (isa<EnumConstantDecl>(valueDecl)) {
      auto ecd = cast<EnumConstantDecl>(valueDecl);
      return convertEnumConst(ecd, locStr);

    } else if (isa<FunctionDecl>(valueDecl)) {
      auto funcDecl = cast<FunctionDecl>(valueDecl);
      std::string funcName = funcDecl->getNameInfo().getAsString();
      ss << "expr.VarE(\"" << stu.convertFuncName(funcName) << "\"";
      ss << ", " << locStr << ")";
      slangExpr.expr = ss.str();
      slangExpr.qualType = funcDecl->getType();
      slangExpr.locStr = locStr;
      return slangExpr;

    } else {
      SLANG_ERROR("Not_a_VarDecl.")
      slangExpr.expr = "ERROR:convertDeclRefExpr";
      return slangExpr;
    }
  } // convertDeclRefExpr()

  // a || b , a && b
  SlangExpr convertLogicalOp(const BinaryOperator *binOp) {
    std::string nextCheck;
    std::string tmpReAssign;
    std::string exitLabel;

    std::string op;
    std::string id = stu.genNextLabelCountStr();
    switch(binOp->getOpcode()) {
      case BO_LOr:
        op = "||";
        nextCheck = id + "NextCheckLor";
        tmpReAssign = id + "TmpAssignLor";
        exitLabel = id + "ExitLor";
        break;
      case BO_LAnd:
        op = "&&";
        nextCheck = id + "NextCheckLand";
        tmpReAssign = id + "TmpAssignLand";
        exitLabel = id + "ExitLand";
        break;
      default: SLANG_ERROR("ERROR:UnknownLogicalOp"); break;
    }

    auto it = binOp->child_begin();
    const Stmt *leftOprStmt = *it;
    ++it;
    const Stmt *rightOprStmt = *it;

    SlangExpr trueValue;
    SlangExpr falseValue;
    trueValue.expr = "expr.LitE(1, " + getLocationString(binOp) + ")";
    falseValue.expr = "expr.LitE(0, " + getLocationString(binOp) + ")";
    trueValue.locStr = falseValue.locStr = getLocationString(binOp);

    // assign tmp = 1
    SlangExpr tmpVar = genTmpVariable("L", "types.Int32", getLocationString(binOp));
    addAssignInstr(tmpVar, trueValue, getLocationString(binOp));

    // check first part a ||, a &&
    SlangExpr leftOprExpr = convertToIfTmp(convertStmt(leftOprStmt));
    if (op == "||") {
      addCondInstr(leftOprExpr.expr, exitLabel, nextCheck, leftOprExpr.locStr);
    } else {
      addCondInstr(leftOprExpr.expr, nextCheck, tmpReAssign, leftOprExpr.locStr);
    }

    // check second part || b, && b
    addLabelInstr(nextCheck);
    SlangExpr rightOprExpr = convertToIfTmp(convertStmt(rightOprStmt));
    addCondInstr(rightOprExpr.expr, exitLabel, tmpReAssign, leftOprExpr.locStr);

    // assign tmp = 0
    addLabelInstr(tmpReAssign);
    addAssignInstr(tmpVar, falseValue, getLocationString(binOp));

    // exit label
    addLabelInstr(exitLabel);

    return tmpVar;
  } // convertLogicalOp()

  SlangExpr convertUnaryIncDecOp(const UnaryOperator *unOp) {
    auto it = unOp->child_begin();
    SlangExpr exprArg = convertStmt(*it);

    std::string op;
    switch(unOp->getOpcode()) {
      case UO_PreInc:
      case UO_PostInc: op = "op.BO_ADD"; break;
      case UO_PostDec:
      case UO_PreDec: op = "op.BO_SUB"; break;
      default:  break;
    }

    SlangExpr litOne;
    litOne.expr = "expr.LitE(1, " + getLocationString(unOp) + ")";
    litOne.locStr = getLocationString(unOp);

    SlangExpr incDecExpr = createBinaryExpr(exprArg, op,
        litOne, getLocationString(unOp), exprArg.qualType);

    switch(unOp->getOpcode()) {
      case UO_PreInc:
      case UO_PreDec: {
        addAssignInstr(exprArg, incDecExpr, getLocationString(unOp));
        return convertToTmp(exprArg, true);
      }

      case UO_PostInc:
      case UO_PostDec: {
        SlangExpr tmpExpr = convertToTmp(exprArg, true);
        addAssignInstr(exprArg, incDecExpr, getLocationString(unOp));
        return tmpExpr;
      }

      default:
        SLANG_ERROR("ERROR:UnknownIncDecOps" <<
            unOp->getOpcodeStr(unOp->getOpcode()));
        break;
    }
    return exprArg;
  }

  SlangExpr convertUnaryOperator(const UnaryOperator *unOp) {
    switch(unOp->getOpcode()) {
      case UO_PreInc:
      case UO_PostInc:
      case UO_PreDec:
      case UO_PostDec:
        return convertUnaryIncDecOp(unOp);
      default:  break;
    }

    SlangExpr exprArg;
    auto it = unOp->child_begin();

    if (unOp->getOpcode() == UO_AddrOf) {
      exprArg = convertStmt(*it); // special case: e.g. &arr[7][5], ...
    } else {
      exprArg = convertToTmp(convertStmt(*it));
    }

    std::string op;
    switch (unOp->getOpcode()) {
      default:
        SLANG_DEBUG("convertUnaryOp: " << unOp->getOpcodeStr(unOp->getOpcode()))
        break;
      case UO_AddrOf: op = "op.UO_ADDROF"; break;
      case UO_Deref: op = "op.UO_DEREF"; break;
      case UO_Minus: op = "op.UO_MINUS"; break;
      case UO_Plus: op = "op.UO_MINUS"; break;
      case UO_LNot: op = "op.UO_LNOT"; break;
      case UO_Not: op = "op.UO_BIT_NOT"; break;
      case UO_Extension:
        exprArg.expr = "expr.LitE(0," + getLocationString(unOp) + ")";
        exprArg.qualType = unOp->getType();
        exprArg.locStr = getLocationString(unOp);
        exprArg.compound = false;
        return exprArg; // don't handle __extension__ expressions
    }

    return createUnaryExpr(op, exprArg, getLocationString(unOp),
        getImplicitType(unOp, unOp->getType()));
  } // convertUnaryOperator()

  SlangExpr convertUnaryExprOrTypeTraitExpr(const UnaryExprOrTypeTraitExpr *stmt) {
    SlangExpr slangExpr;
    SlangExpr innerExpr;
    std::stringstream ss;
    uint64_t size = 0;

    std::string locStr = getLocationString(stmt);

    UnaryExprOrTypeTrait kind = stmt->getKind();
    switch (kind) {
    // the sizeof operator
    case UETT_SizeOf: {
        auto iterator = stmt->child_begin();
        if (iterator != stmt->child_end()) {
            // then child is an expression

            const Stmt *firstChild = *iterator;
            innerExpr = convertStmt(firstChild);
            const Expr *expr = cast<Expr>(firstChild);
            // slangExpr.qualType = Ctx->getTypeOfExprType(const_cast<Expr*>(expr));
            slangExpr.qualType = expr->getType();
            const Type *type = slangExpr.qualType.getTypePtr();
            if (type && !isIncompleteType(type)) {
                TypeInfo typeInfo = Ctx->getTypeInfo(slangExpr.qualType);
                size = typeInfo.Width / 8;
            } else {
                // FIXME: handle runtime sizeof support too
                SLANG_ERROR("SizeOf_Expr_is_incomplete. Loc:" << locStr)
            }
        } else {
            // child is a type
            slangExpr.qualType = stmt->getType();
            TypeInfo typeInfo = Ctx->getTypeInfo(
                stmt->getArgumentType());
            size = typeInfo.Width / 8;
        }

        ss << "expr.LitE(";
        if (size == 0) {
            ss << "ERROR:sizeof()";
        } else {
            ss << size;
        }
        ss << ", " << locStr << ")";
        slangExpr.expr = ss.str();
        break;
    }

    default:
        SLANG_ERROR("UnaryExprOrTypeTrait not handled. Kind: " << kind)
        break;
    }
    return slangExpr;
  } // convertUnaryExprOrTypeTraitExpr()

  SlangExpr convertBinaryOperator(const BinaryOperator *binOp) {
    SlangExpr slangExpr;

    if (binOp->isCompoundAssignmentOp()) {
      return convertCompoundAssignmentOp(binOp);
    } else if (binOp->isAssignmentOp()) {
      return convertAssignmentOp(binOp);
    } else if (binOp->isLogicalOp()) {
      return convertLogicalOp(binOp);
    }

    std::string op;
    switch (binOp->getOpcode()) {
    // NOTE : && and || are handled in convertConditionalOp()

    case BO_Add: op = "op.BO_ADD"; break;
    case BO_Sub: op = "op.BO_SUB"; break;
    case BO_Mul: op = "op.BO_MUL"; break;
    case BO_Div: op = "op.BO_DIV"; break;
    case BO_Rem: op = "op.BO_MOD"; break;

    case BO_LT: op = "op.BO_LT"; break;
    case BO_LE: op = "op.BO_LE"; break;
    case BO_EQ: op = "op.BO_EQ"; break;
    case BO_NE: op = "op.BO_NE"; break;
    case BO_GE: op = "op.BO_GE"; break;
    case BO_GT: op = "op.BO_GT"; break;

    case BO_Or: op = "op.BO_BIT_OR"; break;
    case BO_And: op = "op.BO_BIT_AND"; break;
    case BO_Xor: op = "op.BO_BIT_XOR"; break;

    case BO_Shl: op = "op.BO_LSHIFT"; break;
    case BO_Shr: op = "op.BO_RSHIFT"; break;

    case BO_Comma: return convertBinaryCommaOp(binOp);

    default: op = "ERROR:binOp"; break;
    }

    auto it = binOp->child_begin();
    const Stmt *leftOprStmt = *it;
    ++it;
    const Stmt *rightOprStmt = *it;

    SlangExpr leftOprExpr = convertStmt(leftOprStmt);
    SlangExpr rightOprExpr = convertStmt(rightOprStmt);

    slangExpr = createBinaryExpr(leftOprExpr,
        op, rightOprExpr, getLocationString(binOp),
        getImplicitType(binOp, binOp->getType()));

    return slangExpr;
  } // convertBinaryOperator()

  // stores the given expression into a tmp variable
  SlangExpr convertToTmp(SlangExpr slangExpr, bool force = false) {
    if (slangExpr.compound || force == true) {
      SlangExpr tmpExpr;
      if (slangExpr.qualType.isNull() || slangExpr.qualType.getTypePtr()->isVoidType()) {
        tmpExpr = genTmpVariable("t", "types.Int32", slangExpr.locStr);
      } else {
        if (slangExpr.qualType.getTypePtr()->isArrayType()) {
          // for array type, generate a tmp variable which is a pointer
          // to its element types.
          const Type *type = slangExpr.qualType.getTypePtr();
          const ArrayType *arrayType = type->getAsArrayTypeUnsafe();
          QualType elementType = arrayType->getElementType();
          QualType tmpVarType = Ctx->getPointerType(elementType);
          tmpExpr = genTmpVariable("t", tmpVarType, slangExpr.locStr);
        } else if (slangExpr.qualType.getTypePtr()->isFunctionType()) {
          // create a tmp variable which is a pointer to the function type
          QualType tmpVarType = Ctx->getPointerType(slangExpr.qualType);
          tmpExpr = genTmpVariable("t", tmpVarType, slangExpr.locStr);
        } else {
          tmpExpr = genTmpVariable("t", slangExpr.qualType, slangExpr.locStr);
        }
      }
      std::stringstream ss;

      ss << "instr.AssignI(" << tmpExpr.expr << ", " << slangExpr.expr;
      ss << ", " << slangExpr.locStr << ")"; // close instr.AssignI(...
      stu.addStmt(ss.str());

      return tmpExpr;
    } else {
      return slangExpr;
    }
  } // convertToTmp()

  // stores the given expression into a tmp variable
  BitEntity* convertToTmpBit(BitExpr* bitExpr, bool force = false) {
    if (isBitExprCompoundBit(bitExpr) || force == true) {
      SlangExpr tmpExpr;
      if (slangExpr.qualType.isNull() || slangExpr.qualType.getTypePtr()->isVoidType()) {
        tmpExpr = genTmpVariableBit(K_VK_TINT32, "t", bitExpr->loc());
      } else {
        if (slangExpr.qualType.getTypePtr()->isArrayType()) {
          // for array type, generate a tmp variable which is a pointer
          // to its element types.
          const Type *type = slangExpr.qualType.getTypePtr();
          const ArrayType *arrayType = type->getAsArrayTypeUnsafe();
          QualType elementType = arrayType->getElementType();
          QualType tmpVarType = Ctx->getPointerType(elementType);
          tmpExpr = genTmpVariable("t", tmpVarType, slangExpr.locStr);
        } else if (slangExpr.qualType.getTypePtr()->isFunctionType()) {
          // create a tmp variable which is a pointer to the function type
          QualType tmpVarType = Ctx->getPointerType(slangExpr.qualType);
          tmpExpr = genTmpVariable("t", tmpVarType, slangExpr.locStr);
        } else {
          tmpExpr = genTmpVariable("t", slangExpr.qualType, slangExpr.locStr);
        }
      }
      std::stringstream ss;

      ss << "instr.AssignI(" << tmpExpr.expr << ", " << slangExpr.expr;
      ss << ", " << slangExpr.locStr << ")"; // close instr.AssignI(...
      stu.addStmt(ss.str());

      return tmpExpr;
    } else {
      return slangExpr;
    }
  } // convertToTmpBit()

  // stores the given expression into a tmp variable
  SlangExpr convertToTmp2(SlangExpr slangExpr, bool force = false) {

    if (slangExpr.compound || force == true) {
      bool takeAddress = false;
      SlangExpr tmpExpr;
      if (slangExpr.qualType.isNull() || slangExpr.qualType.getTypePtr()->isVoidType()) {
        tmpExpr = genTmpVariable("t", "types.Int32", slangExpr.locStr);
      } else {
        if (slangExpr.qualType.getTypePtr()->isArrayType()) {
          // for array type, generate a tmp variable which is a pointer
          // to its element types.
          const Type *type = slangExpr.qualType.getTypePtr();
          const ArrayType *arrayType = type->getAsArrayTypeUnsafe();
          QualType elementType = arrayType->getElementType();
          QualType tmpVarType = Ctx->getPointerType(elementType);
          tmpExpr = genTmpVariable("t", tmpVarType, slangExpr.locStr);
        } else if (slangExpr.qualType.getTypePtr()->isFunctionType()) {
          // create a tmp variable which is a pointer to the function type
          QualType tmpVarType =
              Ctx->getPointerType(slangExpr.qualType);
          tmpExpr = genTmpVariable("t", tmpVarType, slangExpr.locStr);
        } else if (slangExpr.qualType.getTypePtr()->isRecordType()) {
          takeAddress = true;
          tmpExpr = genTmpVariable("t",
                                   Ctx->getPointerType(slangExpr.qualType),
                                   slangExpr.locStr);
        } else {
          tmpExpr = genTmpVariable("t", slangExpr.qualType, slangExpr.locStr);
        }
      }
      std::stringstream ss;

      if (takeAddress) {
        ss << "instr.AssignI(" << tmpExpr.expr << ", ";
        ss << "expr.AddrOfE(" << slangExpr.expr << ", " << slangExpr.locStr << ")";
        ss << ", " << slangExpr.locStr << ")"; // close instr.AssignI(...
      } else {
        ss << "instr.AssignI(" << tmpExpr.expr << ", " << slangExpr.expr;
        ss << ", " << slangExpr.locStr << ")"; // close instr.AssignI(...
      }
      stu.addStmt(ss.str());

      return tmpExpr;
    } else {
      return slangExpr;
    }
  } // convertToTmp2()

  // special tmp variable for if "t.1if", "t.2if" etc...
  SlangExpr convertToIfTmp(SlangExpr slangExpr, bool force = false) {
    if (slangExpr.compound || force == true) {
      SlangExpr tmpExpr;
      if (slangExpr.qualType.isNull()) {
        tmpExpr = genTmpVariable("if", "types.Int32", slangExpr.locStr);
      } else {
        tmpExpr = genTmpVariable("if", slangExpr.qualType, slangExpr.locStr);
      }
      std::stringstream ss;

      ss << "instr.AssignI(" << tmpExpr.expr << ", " << slangExpr.expr;
      ss << ", " << slangExpr.locStr << ")"; // close instr.AssignI(...
      stu.addStmt(ss.str());

      return tmpExpr;
    } else {
      return slangExpr;
    }
  } // convertToIfTmp()

  SlangExpr convertCompoundAssignmentOp(const BinaryOperator *binOp) {
    auto it = binOp->child_begin();
    const Stmt *lhs = *it;
    const Stmt *rhs = *(++it);

    SlangExpr rhsExpr = convertStmt(rhs);
    SlangExpr lhsExpr = convertStmt(lhs);

    if (lhsExpr.compound && rhsExpr.compound) {
      rhsExpr = convertToTmp(rhsExpr);
    }

    std::string op;
    switch(binOp->getOpcode()) {
      case BO_ShlAssign: op = "op.BO_LSHIFT"; break;
      case BO_ShrAssign: op = "op.BO_RSHIFT"; break;

      case BO_OrAssign: op = "op.BO_BIT_OR"; break;
      case BO_AndAssign: op = "op.BO_BIT_AND"; break;
      case BO_XorAssign: op = "op.BO_BIT_XOR"; break;

      case BO_AddAssign: op = "op.BO_ADD"; break;
      case BO_SubAssign: op = "op.BO_SUB"; break;
      case BO_MulAssign: op = "op.BO_MUL"; break;
      case BO_DivAssign: op = "op.BO_DIV"; break;
      case BO_RemAssign: op = "op.BO_MOD"; break;

      default: op = "ERROR:UnknowncompoundAssignOp"; break;
    }

    SlangExpr newRhsExpr;
    if (lhsExpr.compound) {
      newRhsExpr = convertToTmp(createBinaryExpr(
          lhsExpr, op, rhsExpr, getLocationString(binOp),
          lhsExpr.qualType));
    } else {
      newRhsExpr = createBinaryExpr(
          lhsExpr, op, rhsExpr, getLocationString(binOp),
          lhsExpr.qualType);
    }

    addAssignInstr(lhsExpr, newRhsExpr, getLocationString(binOp));
    return lhsExpr;
  } // convertCompoundAssignmentOp()

  SlangExpr convertAssignmentOp(const BinaryOperator *binOp) {
    SlangExpr lhsExpr, rhsExpr;

    auto it = binOp->child_begin();
    const Stmt *lhs = *it;
    const Stmt *rhs = *(++it);

    rhsExpr = convertStmt(rhs);
    lhsExpr = convertStmt(lhs);

    if (lhsExpr.compound && rhsExpr.compound) {
      rhsExpr = convertToTmp(rhsExpr);
    }

    addAssignInstr(lhsExpr, rhsExpr, getLocationString(binOp));

    return lhsExpr;
  } // convertAssignmentOp()

  SlangExpr convertCompoundStmt(const CompoundStmt *compoundStmt) {
    SlangExpr slangExpr;

    for (auto it = compoundStmt->body_begin(); it != compoundStmt->body_end(); ++it) {
      // don't care about the return value
      convertStmt(*it);
    }

    return slangExpr;
  } // convertCompoundStmt()

  SlangExpr convertParenExpr(const ParenExpr *parenExpr) {
    auto it = parenExpr->child_begin(); // should have only one child
    return convertStmt(*it);
  } // convertParenExpr()

  SlangExpr convertLabel(const LabelStmt *labelStmt) {
    SlangExpr slangExpr;
    std::stringstream ss;

    std::string locStr = getLocationString(labelStmt);

    auto firstChild = *labelStmt->child_begin();
    if (isa<CaseStmt>(firstChild) && stu.switchCfls) {
      stu.switchCfls->gotoLabel = labelStmt->getName();
      stu.switchCfls->gotoLabelLocStr = locStr;
      llvm::errs() << "ERROR:LABEL_BEFORE_CASE(CheckTheCFG): " << stu.switchCfls->gotoLabel << "\n";
    } else {
      ss << "instr.LabelI(\"" << labelStmt->getName() << "\"";
      ss << ", " << locStr << ")"; // close instr.LabelI(...
      stu.addStmt(ss.str());
    }

    for (auto it = labelStmt->child_begin(); it != labelStmt->child_end(); ++it) {
      convertStmt(*it);
    }

    return slangExpr;
  } // convertLabel()

  // BOUND START: type_conversion_routines

  // converts clang type to span ir types
  std::string convertClangType(QualType qt) {
    std::stringstream ss;

    if (qt.isNull()) {
      return "types.Int32"; // the default type
    }

    qt = getCleanedQualType(qt);

    const Type *type = qt.getTypePtr();

    if (type->isBuiltinType()) {
      return convertClangBuiltinType(qt);

    } else if (type->isEnumeralType()) {
      ss << "types.Int32";

    } else if (type->isFunctionPointerType()) {
      // should be before ->isPointerType() check below
      return convertFunctionPointerType(qt);

    } else if (type->isPointerType()) {
      ss << "types.Ptr(to=";
      QualType pqt = type->getPointeeType();
      ss << convertClangType(pqt);
      ss << ")";

    } else if (type->isRecordType()) {
      SlangRecord *slangRecordType;
      if (type->isStructureType()) {
        return convertClangRecordType(type->getAsStructureType()->getDecl(),
            slangRecordType);
      } else if (type->isUnionType()) {
        return convertClangRecordType(type->getAsUnionType()->getDecl(),
            slangRecordType);
      } else {
        ss << "ERROR:RecordType";
      }

    } else if (type->isArrayType()) {
      return convertClangArrayType(qt);

    } else if (type->isFunctionProtoType()) {
      return convertFunctionPrototype(qt);

    } else {
      ss << "ERROR:UnknownType.";
    }

    return ss.str();
  } // convertClangType()

  // converts clang type to span ir types
  // Returns 0 if successful, non-zero if error
  int convertClangTypeBit(QualType qt, BitDataType *dt) {
    int success = 0;

    if (qt.isNull()) {
      dt->set_vkind(K_VK::INT32);
      return 0;
    }

    qt = getCleanedQualType(qt);

    const Type *type = qt.getTypePtr();

    //delit: remove this condition and body
    if (!type->isBuiltinType()) {
      return 11;
    }

    if (type->isBuiltinType()) {
      return convertClangBuiltinTypeBit(qt, dt);

    } else if (type->isEnumeralType()) {
      dt->set_vkind(K_VK::INT32); // Default to int32

    } else if (type->isFunctionPointerType()) {
      // should be before ->isPointerType() check below
      return convertFunctionPointerTypeBit(qt, dt);

    } else if (type->isPointerType()) {
      QualType pqt = type->getPointeeType();
      BitDataType *pdt = new BitDataType();
      success = convertClangTypeBit(pqt, pdt);
      if (success != 0) {
        return success;
      }
      dt->set_vkind(getPtrKindBit(pdt->vkind()));
      dt->set_allocated_subtype(pdt);

    } else if (type->isRecordType()) {
      if (type->isStructureType()) {
        success = convertClangRecordTypeBit(type->getAsStructureType()->getDecl(), dt);
      } else if (type->isUnionType()) {
        success = convertClangRecordTypeBit(type->getAsUnionType()->getDecl(), dt);
      } else {
        success = 120;
      }

    } else if (type->isArrayType()) {
      success = convertClangArrayTypeBit(qt, dt);

    } else if (type->isFunctionProtoType()) {
      success = convertFunctionPrototypeBit(qt, dt);

    } else {
      success = 121;
    }

    return success;
  } // convertClangTypeBit()

  // Returns the pointer kind for the given pointee kind
  K_VK getPtrKindBit(K_VK pointeeKind) {
    switch (pointeeKind) {
      case K_VK::INT8: return K_VK::PTR_TO_INT;
      case K_VK::INT16: return K_VK::PTR_TO_INT;
      case K_VK::INT32: return K_VK::PTR_TO_INT;
      case K_VK::INT64: return K_VK::PTR_TO_INT;
      case K_VK::FLOAT16: return K_VK::PTR_TO_FLOAT;
      case K_VK::FLOAT32: return K_VK::PTR_TO_FLOAT;
      case K_VK::FLOAT64: return K_VK::PTR_TO_FLOAT;
      case K_VK::VOID: return K_VK::PTR_TO_VOID;
      case K_VK::PTR: return K_VK::PTR_TO_PTR;
      case K_VK::UNION: return K_VK::PTR_TO_RECORD;
      case K_VK::STRUCT: return K_VK::PTR_TO_RECORD;
      case K_VK::ARR_FIXED: return K_VK::PTR_TO_ARR;
      case K_VK::ARR_VARIABLE: return K_VK::PTR_TO_ARR;
      case K_VK::ARR_PARTIAL: return K_VK::PTR_TO_ARR;
      default: return K_VK::PTR_TO_VOID;
    }
  }

  std::string convertClangBuiltinType(QualType qt) {
    std::stringstream ss;

    const Type *type = qt.getTypePtr();

    if (type->isSignedIntegerType()) {
      if (type->isCharType()) {
        ss << "types.Int8";
      } else if (type->isChar16Type()) {
        ss << "types.Int16";
      } else if (type->isIntegerType()) {
        TypeInfo typeInfo = Ctx->getTypeInfo(qt);
        size_t size = typeInfo.Width;
        ss << "types.Int" << size;
      } else {
        ss << "ERROR:UnknownSignedIntType.";
      }

    } else if (type->isUnsignedIntegerType()) {
      if (type->isCharType()) {
        ss << "types.UInt8";
      } else if (type->isChar16Type()) {
        ss << "types.UInt16";
      } else if (type->isIntegerType()) {
        TypeInfo typeInfo = Ctx->getTypeInfo(qt);
        size_t size = typeInfo.Width;
        ss << "types.UInt" << size;
      } else {
        ss << "ERROR:UnknownUnsignedIntType.";
      }

    } else if (type->isFloatingType()) {
      ss << "types.Float64";  // FIXME: all are considered 64 bit (okay for analysis purposes)
    } else if (type->isVoidType()) {
      ss << "types.Void";
    } else {
      ss << "ERROR:UnknownBuiltinType.";
    }

    return ss.str();
  } // convertClangBuiltinType()

  // Returns 0 if successful, non-zero if error
  int convertClangBuiltinTypeBit(QualType qt, BitDataType *dt) {
    const Type *type = qt.getTypePtr();

    if (type->isSignedIntegerType()) {
      if (type->isCharType()) {
        dt->set_vkind(K_VK::INT8);
      } else if (type->isChar16Type()) {
        dt->set_vkind(K_VK::INT16);
      } else if (type->isIntegerType()) {
        TypeInfo typeInfo = Ctx->getTypeInfo(qt);
        size_t size = typeInfo.Width;
        if (size == 32) {
          dt->set_vkind(K_VK::INT32);
        } else if (size == 64) {
          dt->set_vkind(K_VK::INT64);
        } else {
          return 100;
        }
      } else {
        return 101;
      }

    } else if (type->isUnsignedIntegerType()) {
      if (type->isCharType()) {
        dt->set_vkind(K_VK::UINT8);
      } else if (type->isChar16Type()) {
        dt->set_vkind(K_VK::UINT16);
      } else if (type->isIntegerType()) {
        TypeInfo typeInfo = Ctx->getTypeInfo(qt);
        size_t size = typeInfo.Width;
        if (size == 32) {
          dt->set_vkind(K_VK::UINT32);
        } else if (size == 64) {
          dt->set_vkind(K_VK::UINT64);
        } else {
          return 102;
        }
      } else {
        return 103;
      }

    } else if (type->isFloatingType()) {
      dt->set_vkind(K_VK::FLOAT64);
    } else if (type->isVoidType()) {
      dt->set_vkind(K_VK::VOID);
    } else {
      return 104;
    }

    return 0;
  } // convertClangBuiltinTypeBit()

  std::string convertClangRecordType(const RecordDecl *recordDecl,
      SlangRecord *&returnSlangRecord) {
    // a hack1 for anonymous decls (it works!) see test 000193.c and its AST!!
    static const RecordDecl *lastAnonymousRecordDecl = nullptr;
    if (recordDecl->getDefinition()) {
      recordDecl = recordDecl->getDefinition();
    }

    if (recordDecl == nullptr) {
      // default to the last anonymous record decl
      return convertClangRecordType(lastAnonymousRecordDecl, returnSlangRecord);
    }

    if (stu.isRecordPresent((uint64_t)recordDecl)) {
      returnSlangRecord = &stu.getRecord((uint64_t)recordDecl); // return pointer back
      return stu.getRecord((uint64_t)recordDecl).toShortString();
    }

    std::string namePrefix;
    SlangRecord slangRecord;

    if (recordDecl->isStruct()) {
      namePrefix = "s:";
      slangRecord.recordKind = Struct;
    } else if (recordDecl->isUnion()) {
      namePrefix = "u:";
      slangRecord.recordKind = Union;
    }

    if (recordDecl->getNameAsString() == "") {
      slangRecord.anonymous = true;
      slangRecord.name = namePrefix + stu.getNextRecordIdStr();
    } else {
      slangRecord.anonymous = false;
      slangRecord.name = namePrefix + recordDecl->getNameAsString();
    }

    slangRecord.locStr = getLocationString(recordDecl);

    stu.addRecord((uint64_t)recordDecl, slangRecord);                  // IMPORTANT
    SlangRecord &newSlangRecord = stu.getRecord((uint64_t)recordDecl); // IMPORTANT
    returnSlangRecord = &newSlangRecord; // IMPORTANT

    SlangRecordField slangRecordField;

    SlangRecord *getBackSlangRecord;
    for (auto it = recordDecl->decls_begin(); it != recordDecl->decls_end(); ++it) {
      if (isa<RecordDecl>(*it)) {
        convertClangRecordType(cast<RecordDecl>(*it), getBackSlangRecord);
      } else if (isa<FieldDecl>(*it)) {
        const FieldDecl *fieldDecl = cast<FieldDecl>(*it);

        slangRecordField.clear();

        if (fieldDecl->getNameAsString() == "") {
          slangRecordField.name = newSlangRecord.getNextAnonymousFieldIdStr() + "a";
          slangRecordField.anonymous = true;
        } else {
          slangRecordField.name = fieldDecl->getNameAsString();
          slangRecordField.anonymous = false;
        }

        slangRecordField.type = fieldDecl->getType();
        if (slangRecordField.anonymous) {
          auto slangVar = SlangVar((uint64_t) fieldDecl, slangRecordField.name);
          stu.addVar((uint64_t) fieldDecl, slangVar);
          slangRecordField.typeStr = convertClangRecordType(nullptr,
              slangRecordField.slangRecord);

        } else if (fieldDecl->getType()->isRecordType()) {
          auto type = fieldDecl->getType();
          if (type->isStructureType()) {
            slangRecordField.typeStr =
                convertClangRecordType(type->getAsStructureType()->getDecl(),
                   slangRecordField.slangRecord);
          } else if (type->isUnionType()) {
            slangRecordField.typeStr =
                convertClangRecordType(type->getAsUnionType()->getDecl(),
                    slangRecordField.slangRecord);
          }
        } else {
          slangRecordField.typeStr = convertClangType(slangRecordField.type);
        }

        newSlangRecord.members.push_back(slangRecordField);
      }
    }

    // store for later use (part-of-hack1))
    lastAnonymousRecordDecl = recordDecl;

    // no need to add newSlangRecord, its a reference to its entry in the stu.recordMap
    return newSlangRecord.toShortString();
  } // convertClangRecordType()

  int convertClangRecordTypeBit(const RecordDecl *recordDecl, BitDataType *dt) {
    int success = 0;
    // a hack1 for anonymous decls (it works!) see test 000193.c and its AST!!
    static const RecordDecl *lastAnonymousRecordDecl = nullptr;

    if (recordDecl->getDefinition()) {
      recordDecl = recordDecl->getDefinition();
    }

    if (recordDecl == nullptr) {
      // default to the last anonymous record decl
      return convertClangRecordTypeBit(lastAnonymousRecordDecl, dt);
    }

    if (stu.isRecordPresentBit((uint64_t)recordDecl)) {
      // Get existing record
      const auto& bitEntityInfo = stu.bittu.entityinfo().at((uint64_t)recordDecl);
      dt->set_typeid_(bitEntityInfo.dt().typeid_());
      dt->set_typename_(bitEntityInfo.dt().typename_());
      return 0;
    }

    std::string namePrefix;
    SlangRecord slangRecord;

    if (recordDecl->isStruct()) {
      namePrefix = "s:";
      dt->set_vkind(K_VK::TSTRUCT);
    } else if (recordDecl->isUnion()) {
      namePrefix = "u:";
      dt->set_vkind(K_VK::TUNION);
    }

    if (recordDecl->getNameAsString() == "") {
      dt->set_anonymous(true);
      dt->set_typename_(namePrefix + stu.getNextRecordIdStr());
    } else {
      dt->set_anonymous(false);
      dt->set_typename_(namePrefix + recordDecl->getNameAsString());
    }

    BitEntityInfo bitEntityInfo;
    bitEntityInfo.set_ekind(K_EK::EDATA_TYPE);
    bitEntityInfo.set_eid((uint64_t)recordDecl);
    bitEntityInfo.set_allocated_dt(dt);
    bitEntityInfo.set_allocated_loc(getSrcLocBit(recordDecl));
    bitEntityInfo.set_strval(dt->typename_());
    stu.bittu.mutable_entityinfo()->emplace((uint64_t)recordDecl, bitEntityInfo);

    BitDataType* recordedDT = stu.bittu.mutable_entityinfo()->at((uint64_t)recordDecl).mutable_dt();

    //stu.addRecord((uint64_t)recordDecl, slangRecord);                  // IMPORTANT
    //SlangRecord &newSlangRecord = stu.getRecord((uint64_t)recordDecl); // IMPORTANT
    //returnSlangRecord = &newSlangRecord; // IMPORTANT

    SlangRecordField slangRecordField;

    for (auto it = recordDecl->decls_begin(); it != recordDecl->decls_end(); ++it) {
      if (isa<RecordDecl>(*it)) {
        BitDataType* subRecordDT = new BitDataType();
        convertClangRecordTypeBit(cast<RecordDecl>(*it), subRecordDT);
      } else if (isa<FieldDecl>(*it)) {
        const FieldDecl *fieldDecl = cast<FieldDecl>(*it);
        BitDataType fieldDT;
        std::string fieldName;

        if (fieldDecl.getNameAsString() == "") {
          fieldDT.set_anonymous(true);
          fieldName = ::slang::Util::getNextUniqueIdStr() + "a";
        } else {
          fieldDT.set_anonymous(false);
          fieldName = fieldDecl->getNameAsString();
        }
        fieldDT.set_typename_(fieldName);

        if (fieldDT.anonymous()) {
          success = convertClangRecordTypeBit(nullptr, fieldDT);
          if (success != 0) {
            return success;
          }
          BitEntityInfo bitEntityInfo;
          bitEntityInfo.set_ekind(K_EK::ERECORD_FIELD);
          bitEntityInfo.set_eid((uint64_t) fieldDecl);
          bitEntityInfo.set_parentid((uint64_t)recordDecl);
          bitEntityInfo.set_allocated_dt(fieldDT);
          bitEntityInfo.set_strval(fieldDT.typename_());
          bitEntityInfo.set_allocated_loc(getSrcLocBit(fieldDecl));
          stu.bittu.mutable_entityinfo()->emplace((uint64_t) fieldDecl, bitEntityInfo);
        } else if (fieldDecl->getType()->isRecordType()) {
          auto type = fieldDecl->getType();
          if (type->isStructureType()) {
            success = convertClangRecordTypeBit(type->getAsStructureType()->getDecl(), fieldDT);
          } else if (type->isUnionType()) {
            success = convertClangRecordTypeBit(type->getAsUnionType()->getDecl(), fieldDT);
          }
          if (success != 0) {
            return success;
          }
        } else {
          success = convertClangTypeBit(fieldDecl->getType(), fieldDT);
        }

        recordedDT->mutable_fopIds()->Add((uint64_t) fieldDecl);
        recordedDT->mutable_fopTypes()->Add(fieldDT);
      }
    }

    // store for later use (part-of-hack1))
    lastAnonymousRecordDecl = recordDecl;

    return success;
  } // convertClangRecordTypeBit()

  std::string convertClangArrayType(QualType qt) {
    std::stringstream ss;

    const Type *type = qt.getTypePtr();
    const ArrayType *arrayType = type->getAsArrayTypeUnsafe();

    if (isa<ConstantArrayType>(arrayType)) {
      ss << "types.ConstSizeArray(of=";
      ss << convertClangType(arrayType->getElementType());
      ss << ", ";
      auto constArrType = cast<ConstantArrayType>(arrayType);
      auto size = constArrType->getSize();
      charSv->clear(); size.toString(*charSv, 10, false);
      ss << "size=" << charSv->data();
      ss << ")";

    } else if (isa<VariableArrayType>(arrayType)) {
      ss << "types.VarArray(of=";
      ss << convertClangType(arrayType->getElementType());
      ss << ")";
    } else if (isa<IncompleteArrayType>(arrayType)) {
      ss << "types.IncompleteArray(of=";
      ss << convertClangType(arrayType->getElementType());
      ss << ")";

    } else {
      ss << "ERROR:UnknownArrayType";
    }

    return ss.str();
  } // convertClangArrayType()

  int convertClangArrayTypeBit(QualType qt, BitDataType *dt) {
    int success = 0;

    const Type *type = qt.getTypePtr();
    const ArrayType *arrayType = type->getAsArrayTypeUnsafe();

    if (isa<ConstantArrayType>(arrayType)) {
      dt->set_vkind(K_VK::TARR_FIXED);
      auto constArrType = cast<ConstantArrayType>(arrayType);
      auto size = constArrType->getSize();
      // Convert llvm::APInt to uint32_t safely
      uint64_t sizeVal = size.getLimitedValue(UINT32_MAX);
      if (sizeVal > UINT32_MAX) {
        SLANG_FATAL("Array size too large");
        return 106;
      }
      dt->set_len(static_cast<uint32_t>(sizeVal));
    } else if (isa<VariableArrayType>(arrayType)) {
      dt->set_vkind(K_VK::TARR_VARIABLE);
    } else if (isa<IncompleteArrayType>(arrayType)) {
      dt->set_vkind(K_VK::TARR_PARTIAL);
    } else {
      SLANG_FATAL("Unknown array type");
      success = 105;
    }

    BitDataType *elemType = new BitDataType();
    success = convertClangTypeBit(arrayType->getElementType(), elemType);
    if (success != 0) {
      return success;
    }
    dt->set_allocated_subtype(elemType);

    return success;
  } // convertClangArrayType()

  std::string convertFunctionPrototype(QualType qt) {
    std::stringstream ss;

    const Type *funcType = qt.getTypePtr();

    funcType = funcType->getUnqualifiedDesugaredType();
    if (isa<FunctionProtoType>(funcType)) {
      auto funcProtoType = cast<FunctionProtoType>(funcType);
      ss << "types.FuncSig(returnType=";
      ss << convertClangType(funcProtoType->getReturnType());
      ss << ", "
         << "paramTypes=[";
      std::string prefix = "";
      for (auto qType : funcProtoType->getParamTypes()) {
        ss << prefix << convertClangType(qType);
        if (prefix == "")
          prefix = ", ";
      }
      ss << "]";
      if (funcProtoType->isVariadic()) {
        ss << ", variadic=True";
      }
      ss << ")"; // close types.FuncSig(...

    } else {
      ss << "ERROR:UnknownFunctionProtoType";
    }

    return ss.str();
  } // convertFunctionPrototype()

  int convertFunctionPrototypeBit(QualType qt, BitDataType *dt) {
    int success = 0;
    const Type *funcType = qt.getTypePtr();

    funcType = funcType->getUnqualifiedDesugaredType();
    if (isa<FunctionProtoType>(funcType)) {
      auto funcProtoType = cast<FunctionProtoType>(funcType);
      BitDataType *retType = new BitDataType();
      success = convertClangTypeBit(funcProtoType->getReturnType(), retType);
      if (success != 0) {
        return success;
      }
      dt->set_allocated_subtype(retType);

      for (auto qType : funcProtoType->getParamTypes()) {
        BitDataType *paramType = new BitDataType();
        success = convertClangTypeBit(qType, paramType);
        if (success != 0) {
          return success;
        }
        dt->mutable_types()->AddAllocated(paramType);
      }

      if (funcProtoType->isVariadic()) {
        dt->set_variadic(true);
      }

    } else {
      SLANG_FATAL("Unknown function prototype type");
      success = 112;
    }

    return success;
  } // convertFunctionPrototypeBit()

  std::string convertFunctionPointerType(QualType qt) {
    std::stringstream ss;

    const Type *type = qt.getTypePtr();

    ss << "types.Ptr(to=";
    const Type *funcType = type->getPointeeType().getTypePtr();
    funcType = funcType->getUnqualifiedDesugaredType();
    if (isa<FunctionProtoType>(funcType)) {
      auto funcProtoType = cast<FunctionProtoType>(funcType);
      ss << "types.FuncSig(returnType=";
      ss << convertClangType(funcProtoType->getReturnType());
      ss << ", "
         << "paramTypes=[";
      std::string prefix = "";
      for (auto qType : funcProtoType->getParamTypes()) {
        ss << prefix << convertClangType(qType);
        if (prefix == "")
          prefix = ", ";
      }
      ss << "]";
      if (funcProtoType->isVariadic()) {
        ss << ", variadic=True";
      }
      ss << ")"; // close types.FuncSig(...
      ss << ")"; // close types.Ptr(...

    } else if (isa<FunctionNoProtoType>(funcType)) {
      ss << "types.FuncSig(returnType=types.Int32)";
      ss << ")"; // close types.Ptr(...

    } else if (isa<FunctionType>(funcType)) {
      ss << "FuncType";

    } else {
      ss << "ERROR:UnknownFunctionPtrType";
    }

    return ss.str();
  } // convertFunctionPointerType()

  // Returns 0 if successful, non-zero if error
  int convertFunctionPointerTypeBit(QualType qt, BitDataType *dt) {
    int success = 0;
    const Type *type = qt.getTypePtr();
    const Type *funcType = type->getPointeeType().getTypePtr();
    funcType = funcType->getUnqualifiedDesugaredType();

    BitDataType *bitFuncType = new BitDataType();
    if (isa<FunctionProtoType>(funcType)) {
      success = convertFunctionPrototypeBit(qt, bitFuncType);
      if (success != 0) {
        return success;
      }

    } else if (isa<FunctionNoProtoType>(funcType)) {
      // With no function prototype, assume int32 return type with no parameters
      BitDataType *retType = new BitDataType();
      retType->set_vkind(K_VK::INT32);
      bitFuncType->set_allocated_subtype(retType);

    } else if (isa<FunctionType>(funcType)) {
      success = 110; // A FuncType -- not expected

    } else {
      success = 111; // Unknown function pointer type
    }

    dt->set_vkind(K_VK::PTR_TO_FUNC);
    dt->set_allocated_subtype(bitFuncType);
    return success;
  } // convertFunctionPointerTypeBit()

  // BOUND END  : type_conversion_routines
  // BOUND END  : conversion_routines

  // BOUND START: helper_routines

  // T can be a Stmt, VarDecl, ValueDecl, or any class that has getBeginLoc()
  // method.
  template <typename T>
  BitSrcLoc getSrcLoc(const T *decl) {
    BitSrcLoc loc;
  
    loc.set_line(
        Ctx->getSourceManager().getExpansionLineNumber(decl->getBeginLoc()));
    loc.set_col(
        Ctx->getSourceManager().getExpansionColumnNumber(decl->getBeginLoc()));
  
    return loc;
  }

  // T can be a Stmt, VarDecl, ValueDecl, or any class that has getBeginLoc()
  // method.
  template <typename T>
  BitSrcLoc* getSrcLocBit(const T *decl) {
    BitSrcLoc *loc = new BitSrcLoc();
  
    loc->set_line(
        Ctx->getSourceManager().getExpansionLineNumber(decl->getBeginLoc()));
    loc->set_col(
        Ctx->getSourceManager().getExpansionColumnNumber(decl->getBeginLoc()));
  
    return loc;
  }

  SlangExpr genTmpVariable(std::string suffix, std::string typeStr,
      std::string locStr) {
    std::stringstream ss;
    SlangExpr slangExpr{};

    // STEP 1: Populate a SlangVar object with unique name.
    SlangVar slangVar{};
    slangVar.id = stu.nextUniqueId();
    uint64_t tmpNumbering = stu.nextTmpId();
    ss << "" << tmpNumbering << suffix;
    slangVar.setLocalVarName(ss.str(), stu.getCurrFuncName());
    slangVar.typeStr = typeStr;

    // STEP 2: Add to the var map.
    // FIXME: The var's 'id' here should be small enough to not interfere with uint64_t addresses.
    stu.addVar(slangVar.id, slangVar);

    // STEP 3: generate var expression.
    ss.str(""); // empty the stream
    ss << "expr.VarE(\"" << slangVar.name << "\"";
    ss << ", " << locStr << ")";

    slangExpr.expr = ss.str();
    slangExpr.locStr = locStr;
    // slangExpr.qualType = qt;
    slangExpr.nonTmpVar = false;

    return slangExpr;
  } // genTmpVariable()

  BitEntity* genTmpVariableBit(K_VK vType, std::string suffix, const BitSrcLoc& loc) {
    BitEntity* bitEntity = new BitEntity();
    BitEntityInfo bitEntityInfo;

    // STEP 1: Populate a SlangVar object with unique name.
    bitEntity->set_eid(stu.nextUniqueId());
    bitEntity->set_allocated_loc(new BitSrcLoc(loc));
    bitEntityInfo.set_eid(bitEntity->eid());
    bitEntityInfo.set_ekind(K_EK::EVAR_LOCL_TMP);
    bitEntityInfo.set_vkind(vType);
    bitEntityInfo.set_allocated_loc(new BitSrcLoc(loc));

    // STEP 2: Populate a BitEntityInfo object with unique name.
    std::stringstream ss;
    ss << "" << stu.nextTmpId() << suffix;
    bitEntityInfo.set_strval(ss.str());

    // STEP 3: Add the variable to the TU.
    // FIXME: The var's 'id' here should be small enough to not interfere with uint64_t addresses.
    stu.addVarBit(bitEntity->eid(), &bitEntityInfo);

    return bitEntity;
  } // genTmpVariableBit()

  SlangExpr genTmpVariable(std::string suffix,
      QualType qt, std::string locStr, bool ifTmp = false) {
    std::stringstream ss;
    SlangExpr slangExpr{};

    // STEP 1: Populate a SlangVar object with unique name.
    SlangVar slangVar{};
    slangVar.id = stu.nextUniqueId();
    uint64_t tmpNumbering = stu.nextTmpId();
    ss << "" << tmpNumbering << suffix;
    slangVar.setLocalVarName(ss.str(), stu.getCurrFuncName());
    slangVar.typeStr = convertClangType(qt);

    // STEP 2: Add to the var map.
    // FIXME: The var's 'id' here should be small enough to not interfere with uint64_t addresses.
    stu.addVar(slangVar.id, slangVar);

    // STEP 3: generate var expression.
    ss.str(""); // empty the stream
    ss << "expr.VarE(\"" << slangVar.name << "\"";
    ss << ", " << locStr << ")";

    slangExpr.expr = ss.str();
    slangExpr.locStr = locStr;
    slangExpr.qualType = qt;
    slangExpr.nonTmpVar = false;
    slangExpr.compound = false;

    return slangExpr;
  } // genTmpVariable()

  std::string getLocationString(const Stmt *stmt) {
    std::stringstream ss;
    uint32_t line = 0;
    uint32_t col = 0;

    ss << "Info(Loc(";
    line = Ctx->getSourceManager().getExpansionLineNumber(stmt->getBeginLoc());
    ss << line << ",";
    col = Ctx->getSourceManager().getExpansionColumnNumber(stmt->getBeginLoc());
    ss << col << "))";

    return ss.str();
  }

  std::string getLocationString(const RecordDecl *recordDecl) {
    std::stringstream ss;
    uint32_t line = 0;
    uint32_t col = 0;

    ss << "Info(Loc(";
    line = Ctx->getSourceManager().getExpansionLineNumber(recordDecl->getBeginLoc());
    ss << line << ",";
    col =
        Ctx->getSourceManager().getExpansionColumnNumber(recordDecl->getBeginLoc());
    ss << col << "))";

    return ss.str();
  }

  std::string getLocationString(const ValueDecl *valueDecl) {
    std::stringstream ss;
    uint32_t line = 0;
    uint32_t col = 0;

    ss << "Info(Loc(";
    line = Ctx->getSourceManager().getExpansionLineNumber(valueDecl->getBeginLoc());
    ss << line << ",";
    col = Ctx->getSourceManager().getExpansionColumnNumber(valueDecl->getBeginLoc());
    ss << col << "))";

    return ss.str();
  }

  // Remove qualifiers and typedefs
  QualType getCleanedQualType(QualType qt) {
    if (qt.isNull())
      return qt;
    qt = qt.getCanonicalType();
    qt.removeLocalConst();
    qt.removeLocalRestrict();
    qt.removeLocalVolatile();
    return qt;
  }

  void addGotoInstr(std::string label) {
    std::stringstream ss;
    ss << "instr.GotoI(\"" << label << "\")";
    stu.addStmt(ss.str());
  }

  void addLabelInstr(std::string label) {
    std::stringstream ss;
    ss << "instr.LabelI(\"" << label << "\")";
    stu.addStmt(ss.str());
  }

  void addCondInstr(std::string expr,
      std::string trueLabel, std::string falseLabel, std::string locStr) {
    std::stringstream ss;
    ss << "instr.CondI(" << expr;
    ss << ", \"" << trueLabel << "\"";
    ss << ", \"" << falseLabel << "\"";
    ss << ", " << locStr << ")";
    stu.addStmt(ss.str());
  }

  void addAssignInstr(SlangExpr& lhs, SlangExpr rhs, std::string locStr) {
    std::stringstream ss;
    if (lhs.compound && rhs.compound) {
      rhs = convertToTmp(rhs); // staticLocal init will not generate tmp
    }
    ss << "instr.AssignI(" << lhs.expr;
    ss << ", " << rhs.expr << ", " << locStr << ")";
    stu.addStmt(ss.str());
  }

  void addAssignInstrBit(BitExpr* lhs, BitExpr* rhs) {
    if (isBitExprCompoundBit(lhs) && isBitExprCompoundBit(rhs)) {
      rhs = convertToTmpBit(rhs); // staticLocal init will not generate tmp
    }
    BitInsn* bitInsn = new BitInsn();
    bitInsn->set_allocated_lhs(lhs);
    bitInsn->set_allocated_rhs(rhs);
    bitInsn->set_allocated_loc(new BitSrcLoc(lhs->loc()));
    stu.addStmtBit(bitInsn);
  } // addAssignInstrBit()
  
  bool isBitExprCompoundBit(BitExpr* be) {
    if (be->xkind() == K_XK::VAL) {
      return false;
    } else {
      return true;
    }
  }

  // Note: unlike createBinaryExpr, createUnaryExpr doesn't convert its expr to tmp expr.
  SlangExpr createUnaryExpr(std::string op,
      SlangExpr expr, std::string locStr, QualType qt) {
    SlangExpr unaryExpr;

    std::stringstream ss;

    if (op == "op.UO_ADDROF") {
      ss << "expr.AddrOfE(";
      ss << expr.expr;
      ss << ", " << locStr << ")";
    } else if (op == "op.UO_DEREF") {
      ss << "expr.DerefE(";
      ss << expr.expr;
      ss << ", " << locStr << ")";
    } else {
      ss << "expr.UnaryE(" << op;
      ss << ", " << expr.expr;
      ss << ", " << locStr << ")";
    }

    unaryExpr.expr = ss.str();
    unaryExpr.qualType = qt;
    unaryExpr.compound = true;
    unaryExpr.locStr = locStr;

    return unaryExpr;
  } // createUnaryExpr()

  BitExpr* createUnaryExprBit(BitEntity* opr, K_XK op) {
    BitExpr* unaryExpr = new BitExpr();
    unaryExpr->set_xkind(op);
    unaryExpr->set_allocated_opr1(opr);
    unaryExpr->set_allocated_loc(new BitSrcLoc(opr->loc()));
    return unaryExpr;
  } // createUnaryExprBit()

  SlangExpr createBinaryExpr(SlangExpr lhsExpr,
      std::string op, SlangExpr rhsExpr, std::string locStr,
      QualType qt) {
    SlangExpr binaryExpr;

    lhsExpr = convertToTmp(lhsExpr);
    rhsExpr = convertToTmp(rhsExpr);

    std::stringstream ss;
    ss << "expr.BinaryE(" << lhsExpr.expr;
    ss << ", " << op;
    ss << ", " << rhsExpr.expr;
    ss << ", " << locStr << ")";

    binaryExpr.expr = ss.str();
    binaryExpr.qualType = qt;
    binaryExpr.compound = true;
    binaryExpr.locStr = locStr;

    return binaryExpr;
  } // createBinaryExpr()

  BitExpr* createBinaryExprBit(BitEntity* opr1, K_XK op, BitEntity* opr2) {
    BitExpr* binaryExpr = new BitExpr();
    binaryExpr->set_xkind(op);
    binaryExpr->set_allocated_opr1(opr1);
    binaryExpr->set_allocated_opr2(opr2);
    binaryExpr->set_allocated_loc(new BitSrcLoc(opr1->loc()));
    return binaryExpr;
  } // createBinaryExprBit()

  // If the expression is the child of an implicit cast,
  // the type of implicit cast is returned, else the given qt is returned
  QualType getImplicitType(const Stmt *stmt, QualType qt) {
    const auto &parents = Ctx->getParents(*stmt);
    if (!parents.empty()) {
      const Stmt *stmt1 = parents[0].get<Stmt>();
      if (stmt1) {
        switch (stmt1->getStmtClass()) {
          default:
            return qt; // just return the given type

          case Stmt::ImplicitCastExprClass: {
            const ImplicitCastExpr *iCast = cast<ImplicitCastExpr>(stmt1);
            return iCast->getType();
          } // case
        } // switch
      } // if
    } // if
    return qt; // just return the given type
  } // getImplicitType()

  // If an element is top level, return true.
  // e.g. in statement "x = y = z = 10;" the first "=" from left is top level.
  bool isTopLevel(const Stmt *stmt) {
    const auto &parents = Ctx->getParents(*stmt);
    if (!parents.empty()) {
      const Stmt *stmt1 = parents[0].get<Stmt>();
      if (stmt1) {
        switch (stmt1->getStmtClass()) {
          default:
            return false;

          case Stmt::CaseStmtClass:
          case Stmt::DefaultStmtClass:
          case Stmt::CompoundStmtClass: {
            return true; // top level
          }

          case Stmt::ForStmtClass: {
            auto body = (cast<ForStmt>(stmt1))->getBody();
            return ((uint64_t)body == (uint64_t)stmt);
          }

          case Stmt::DoStmtClass: {
            auto body = (cast<DoStmt>(stmt1))->getBody();
            return ((uint64_t)body == (uint64_t)stmt);
          }

          case Stmt::WhileStmtClass: {
            auto body = (cast<WhileStmt>(stmt1))->getBody();
            return ((uint64_t)body == (uint64_t)stmt);
          }
          case Stmt::IfStmtClass: {
            auto then_ = (cast<IfStmt>(stmt1))->getThen();
            auto else_ = (cast<IfStmt>(stmt1))->getElse();
            return ((uint64_t)then_ == (uint64_t)stmt || (uint64_t)else_ == (uint64_t)stmt);
          }
        }
      } else {
        return false;
      }
    } else {
      return true; // top level
    }
  } // isTopLevel()

  SlangExpr addAndReturnSizeOfInstrExpr(SlangExpr tmpElementVarArr) {
    std::stringstream ss;

    SlangExpr tmpExpr = convertToTmp(tmpElementVarArr);

    SlangExpr sizeOfExpr;
    ss << "expr.SizeOfE(" << tmpExpr.expr;
    ss << ", " << tmpElementVarArr.locStr << ")";
    sizeOfExpr.expr = ss.str();
    sizeOfExpr.qualType = Ctx->UnsignedIntTy;
    sizeOfExpr.compound = true;
    sizeOfExpr.locStr = tmpElementVarArr.locStr;

    SlangExpr slangExpr = convertToTmp(sizeOfExpr);

    return slangExpr;
  }

  // BOUND END  : helper_routines
}; // class SpirGenerator
} // namespace spir

////////////////////////////////////////////////////////////////
// BOUND START: the_ast_visitors
////////////////////////////////////////////////////////////////

class FunctionVisitor : public RecursiveASTVisitor<FunctionVisitor> {
public:
  explicit FunctionVisitor(spir::SpirGenerator *irgen) : irgen(irgen) {
    // Initialize any other members here if needed
  }

  bool VisitFunctionDecl(FunctionDecl *FD) {
    llvm::outs() << "Found function: " << FD->getNameAsString() << "\n";
    irgen->handleFunctionDecl(FD);
    return true;
  }

private:
  spir::SpirGenerator *irgen;
};

class SpanASTConsumer : public ASTConsumer {
public:
  // Main Entry point for the ASTConsumer (entrypoint for the Slang tool)
  void HandleTranslationUnit(ASTContext &Context) override {
    this->irgen = new spir::SpirGenerator(&Context);
    Visitor = new FunctionVisitor(irgen);

    llvm::outs() << "SpanASTConsumer: \n";

    // Initialize the generator: TU name, out file name etc.
    irgen->slangInit(Context.getTranslationUnitDecl());

    // Handle global variables and inits
    irgen->handleGlobalInits(Context.getTranslationUnitDecl());

    // Handle function declarations and definitions
    //delit Visitor->TraverseDecl(Context.getTranslationUnitDecl());

    // Perform final actions
    irgen->checkEndOfTranslationUnit(Context.getTranslationUnitDecl());
  }

private:
  FunctionVisitor *Visitor;
  spir::SpirGenerator *irgen;
};

class SpanASTAction : public ASTFrontendAction {
public:
  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI,
                                                 StringRef file) override {
    return std::make_unique<SpanASTConsumer>();
  }
};

////////////////////////////////////////////////////////////////
// BOUND END: the_ast_visitors
////////////////////////////////////////////////////////////////

// Entry point for the Slang tool that generates Span IR (spir) from the Clang AST
int main(int argc, const char **argv) {
  // Parse command-line options
  auto ExpectedParser = CommonOptionsParser::create(argc, argv, SlangOptions);
  if (!ExpectedParser) {
    llvm::errs() << ExpectedParser.takeError();
    return 1;
  }
  CommonOptionsParser &OptionsParser = ExpectedParser.get();

  // Print the source files we're processing
  for (const auto& sourcePath : OptionsParser.getSourcePathList()) {
    llvm::outs() << "Processing source file: " << sourcePath << "\n";
  }
  
  // If using a compilation database, also print compilation info
  if (!OptionsParser.getCompilations().getAllCompileCommands().empty()) {
    llvm::outs() << "Using compilation database with "
                << OptionsParser.getCompilations().getAllCompileCommands().size()
                << " entries\n";
                
    // Print command for each source file we're processing
    for (const auto& sourcePath : OptionsParser.getSourcePathList()) {
      auto compileCommands = OptionsParser.getCompilations().getCompileCommands(sourcePath);
      for (const auto& command : compileCommands) {
        llvm::outs() << "  File: " << command.Filename << "\n";
        llvm::outs() << "  Directory: " << command.Directory << "\n";
        llvm::outs() << "  Command: ";
        for (const auto& arg : command.CommandLine) {
          llvm::outs() << arg << " ";
        }
        llvm::outs() << "\n";
      }
    }
  }

  GOOGLE_PROTOBUF_VERIFY_VERSION;

  // Set up ClangTool
  ClangTool Tool(OptionsParser.getCompilations(),
                 OptionsParser.getSourcePathList());

  // Run our FrontendAction
  int success = Tool.run(newFrontendActionFactory<SpanASTAction>().get());

  google::protobuf::ShutdownProtobufLibrary();
  return success;
}