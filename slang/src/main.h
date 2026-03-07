//===----------------------------------------------------------------------===//
//  MIT License.
//  Copyright (c) 2020-2026 The SLANG Authors.
//
//  Author: Anshuman Dhuliya (dhuliya@cse.iitb.ac.in, anshumandhuliya@gmail.com)
//
//===----------------------------------------------------------------------===//
// The slang tool with main() method.
//===----------------------------------------------------------------------===//

#pragma once

#include "clang/AST/Type.h"
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


namespace slang {

typedef std::vector<const Stmt *> StmtVector;
typedef std::vector<std::string> SpanStmtVector;

// the numbering 0,1,2 is important.
enum EdgeLabel { FalseEdge = 0, TrueEdge = 1, UnCondEdge = 2 };
enum SlangRecordKind { Struct = 0, Union = 1 };

// SourceLocation is the source location of an entity in the source file.
// It is not used anywhere, but is useful to pass (line, col) together.
struct SrcLoc {
    uint32_t line;
    uint32_t col;
};

// MayValue is a struct that holds a value and an error code.
// It is used to return a value and an error code from a function.
struct MayValue {
  uint64_t errorCode;
  uint64_t value;

  MayValue() {
    errorCode = 0;
    value = 0;
  }

  MayValue(uint64_t errorCode, uint64_t value = 0) {
    this->errorCode = errorCode;
    this->value = value;
  }

  std::string toString() {
    std::stringstream ss;
    ss << "MayValue: " << value << " (errorCode: " << errorCode << ")";
    return ss.str();
  }
}; // struct MayValue

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
}; // class SlangExpr

class SlangBitExpr {
public:
  spir::BitExpr* bitExpr;
  uint64_t varId;
  QualType qualType;
  bool nonTmpVar;
  bool compound;

  SlangBitExpr() {
    bitExpr = nullptr;
    qualType = QualType();
    varId = 0;
    nonTmpVar = true;
    compound = false;
  };

  std::string toString() {
    std::stringstream ss;
    ss << "SlangBitExpr:\n";
    ss << "  Expr     : " << (bitExpr ? bitExpr->DebugString() : "nullptr") << "\n";
    ss << "  ExprType : " << qualType.getAsString() << "\n";
    ss << "  NonTmpVar: " << (nonTmpVar ? "true" : "false") << "\n";
    ss << "  VarId    : " << varId << "\n";

    return ss.str();
  }

  // Return the original or the clone of the bitExpr object.
  spir::BitExpr* cloneBitExpr() {
    assert(bitExpr != nullptr);
    return new spir::BitExpr(*bitExpr);
  }

  bool deleteBitExpr() {
    if (bitExpr != nullptr) {
      delete bitExpr;
      bitExpr = nullptr;
      return true;
    }
    return false;
  }

  spir::BitSrcLoc srcLoc() {
    spir::BitSrcLoc bsl;
    if (bitExpr != nullptr) {
      bsl.set_line(bitExpr->loc_line());
      bsl.set_col(bitExpr->loc_col());
    }
    return bsl;
  }
}; // class SlangBitExpr

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
    tmpVarCount = 1;
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

// SlangRecord holds a struct or a union record.
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
                           SlangExpr &slangExpr);
  std::string genMemberExpr(std::vector<uint32_t> indexVector);
  std::string toString();
  std::string toShortString();
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

// SlangTU is the translation unit currently being converted.
class SlangTU {
public:
  std::string tuName; // the current translation unit file name
  std::string tuDirectory; // the current translation unit directory
  spir::BitTU bittu; // the bit translation unit
  spir::BitFunc* currBitFunc;

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

  SlangTU()
      : uniqIdCounter{1}, tuName{}, tuDirectory{}, bittu{}, globalInits{}, 
        currFunc{nullptr}, uniqRecordIdCounter{1}, varMap{}, varCountMap{}, funcMap{},
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

  void addStmt(std::string spanStmt);

  // Save the instruction in the global or the current function.
  // Global and function static declarations can be broken into temporary
  // assignments; in such cases the instruction must be added to the global function.
  void addStmtBit(spir::BitInsn* bitInsn);

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

  bool hasTypeKey(uint64_t typeKey) {
    return bittu.datatypes().find(typeKey) != bittu.datatypes().end();
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

  bool isBasicBitType(spir::BitDataType* bitDataType);

  // Add the given entity id and (move) its entity info to the TU.
  void moveAndAddBitEntityInfo(uint64_t eid, spir::BitEntityInfo& bitEntityInfo);

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

  // BOUND START: dump_routines
  // Function to get output filename or error out
  std::string getOutFilename(std::string suffix);
  // dump entire span ir module for the translation unit.
  void dumpSlangIr();
  void dumpHeader(std::stringstream &ss);
  void dumpFooter(std::stringstream &ss);
  void dumpVariables(std::stringstream &ss);
  void dumpGlobalInits(std::stringstream &ss);
  void dumpObjs(std::stringstream &ss);
  void dumpRecords(std::stringstream &ss);
  void dumpFunctions(std::stringstream &ss);
  void writeProtoToFile(const spir::BitTU &bittu, const std::string &filename);
  // BOUND END  : dump_routines

}; // class SlangTU

class SpirGen {
public:
    SpirGen(ASTContext *Ctx);

    // slangInit() sets the meta data like TU name, directory and Clang AST version.
    void slangInit(const TranslationUnitDecl *tuDecl);

    // Handle all global data declarations and initializations 
    // and put their initialization in a special function with id zero (0).
    void handleGlobalInits(const TranslationUnitDecl *tuDecl);
    
    // Handles all variable declarations: both global and local.
    int handleVarDecl(const VarDecl *varDecl, std::string funcName = "");
    void handleValueDecl(const ValueDecl *valueDecl, std::string funcName);
    void handleFunctionDecl(FunctionDecl *D);
    void handleFunctionBody(FunctionDecl *funcDecl);
    const FunctionDecl* handleFuncNameAndType(const FunctionDecl *funcDecl, bool force=false);

    // Entry/Exit Points
    void checkEndOfTranslationUnit(const TranslationUnitDecl *tuDecl);
    void dumpSlangIr();
    void dumpHeader(std::stringstream &ss);
    void dumpFooter(std::stringstream &ss);
    void dumpVariables(std::stringstream &ss);
    void dumpGlobalInits(std::stringstream &ss);

    // Variable and Type Utilities
    void addVar(uint64_t id, const SlangVar &var);
    std::string convertClangType(QualType qt);
    MayValue convertClangTypeBit(QualType qt);
    std::string convertClangArrayType(QualType qt);
    MayValue convertClangArrayTypeBit(QualType qt, const uint64_t typeKey);
    std::string convertFunctionPrototype(QualType qt);
    MayValue convertFunctionPrototypeBit(QualType qt, const uint64_t typeKey);
    std::string convertFunctionPointerType(QualType qt);

    // Statement Conversion
    SlangExpr convertStmt(const Stmt *stmt);
    SlangExpr convertIntegerLiteral(const IntegerLiteral *intLit);
    SlangExpr convertCharacterLiteral(const CharacterLiteral *charLit);
    SlangExpr convertFloatingLiteral(const FloatingLiteral *floatLit);
    SlangExpr convertStringLiteral(const StringLiteral *strLit);
    SlangExpr convertImplicitCastExpr(const ImplicitCastExpr *iCast);
    SlangExpr convertReturnStmt(const ReturnStmt *retStmt);
    SlangExpr convertGotoStmt(const GotoStmt *gotoStmt);
    SlangExpr convertCStyleCastExpr(const CStyleCastExpr *cCast);
    SlangExpr convertMemberExpr(const MemberExpr *memberExpr);
    SlangExpr convertArraySubscriptExpr(const ArraySubscriptExpr *arrayExpr);
    SlangExpr convertUnaryExprOrTypeTraitExpr(const UnaryExprOrTypeTraitExpr *uExpr);
    SlangExpr convertCallExpr(const CallExpr *callExpr);
    SlangExpr convertCompoundStmt(const CompoundStmt *compoundStmt);
    SlangExpr convertAssignmentOp(const BinaryOperator *binOp);
    SlangExpr convertCompoundAssignmentOp(const BinaryOperator *binOp);
    SlangExpr convertBinaryOperator(const BinaryOperator *binOp);
    SlangExpr convertLogicalOp(const BinaryOperator *binOp);
    SlangExpr convertBinaryCommaOp(const BinaryOperator *binOp);
    SlangExpr convertDeclRefExpr(const DeclRefExpr *declRef);
    SlangExpr convertConstantExpr(const ConstantExpr *constExpr);
    SlangExpr convertVarArrayVariable(QualType valueType, QualType elementType);
    SlangExpr convertVariable(const VarDecl *varDecl, std::string locStr = "Info(Loc(33333,33333))");
    SlangExpr convertToTmp(SlangExpr slangExpr, bool force = false);
    SlangExpr convertSlangVar(SlangVar &slangVar, const VarDecl *varDecl);
    SlangExpr convertEnumConst(const EnumConstantDecl *ecd, std::string &locStr);
    SlangExpr convertInitListExprNew(SlangExpr &lhs, const InitListExpr *initListExpr);
    SlangExpr convertContinueStmt(const ContinueStmt *continueStmt);
    SlangExpr convertBreakStmt(const BreakStmt *breakStmt);
    SlangExpr convertDefaultCaseStmt(const DefaultStmt *defaultStmt);
    SlangExpr convertCaseStmt(const CaseStmt *caseStmt);
    SlangExpr convertStmtExpr(const StmtExpr *stmt);
    SlangExpr convertPredefinedExpr(const PredefinedExpr *pe);
    SlangExpr convertLabel(const LabelStmt *labelStmt);
    SlangExpr convertConditionalOp(const ConditionalOperator *condOp);
    SlangExpr convertIfStmt(const IfStmt *ifStmt);
    SlangExpr convertWhileStmt(const WhileStmt *whileStmt);
    SlangExpr convertDoStmt(const DoStmt *doStmt);
    SlangExpr convertForStmt(const ForStmt *forStmt);
    SlangExpr convertUnaryOperator(const UnaryOperator *unOp);
    SlangExpr convertParenExpr(const ParenExpr *parenExpr);
    SlangExpr convertSwitchStmtNew(const SwitchStmt *switchStmt);


    // Bit-level statement variants
    SlangBitExpr convertStmtBit(const Stmt *stmt);
    SlangBitExpr convertUnaryOperatorBit(const UnaryOperator *unOp);
    SlangBitExpr convertBinaryOperatorBit(const BinaryOperator *binOp);
    SlangBitExpr convertCompoundAssignmentOpBit(const BinaryOperator *binOp);
    SlangBitExpr convertAssignmentOpBit(const BinaryOperator *binOp);
    SlangBitExpr convertVarArrayVariableBit(QualType valueType, QualType elementType);
    spir::BitEntity convertVariableBit(const VarDecl *varDecl);
    SlangBitExpr createUnaryBitExpr(spir::K_XK opKind, SlangBitExpr expr, slang::SrcLoc srcLoc, QualType qt);
    SlangBitExpr convertToTmpBitExpr(SlangBitExpr expr, bool force = false, bool gc = false);
    spir::BitEntity *convertClangTypeToBitEntity(QualType qt, uint64_t eid);
    SlangBitExpr createBinaryBitExpr(SlangBitExpr opr1, spir::K_XK op, SlangBitExpr opr2, spir::BitSrcLoc srcLoc, QualType qt);
    spir::BitExpr *createBitExpr(spir::BitEntity be);
    SlangBitExpr convertSlangVarBit(uint64_t eid, const VarDecl *varDecl);
    SlangBitExpr convertPredefinedExprBit(const PredefinedExpr *pe);
    SlangBitExpr convertStmtExprBit(const StmtExpr *stmt);
    SlangBitExpr convertParenExprBit(const ParenExpr *parenExpr);
    // ... Add all other bit-level methods similarly

    // Cast-conversion helpers
    SlangExpr convertCastExpr(const Stmt *expr, QualType qt, std::string locStr);

    // Miscellaneous / Utility
    template <typename T>
    std::string getLocationString(const T *stmt);
    std::string genNextLabelCountStr();
    template <typename T>
    slang::SrcLoc getSrcLocBit(const T *decl);

    // Add instruction emission methods
    void addAssignInstr(SlangExpr &lhs, SlangExpr rhs, std::string locStr);
    void addCondInstrBit(SlangBitExpr expr, spir::BitEntity trueLabel, spir::BitEntity falseLabel, spir::BitSrcLoc srcLoc);
    void addAssignBitInstr(SlangBitExpr lhs, SlangBitExpr rhs);
    void addLabelInstr(const std::string &label);
    void addGotoInstr(const std::string &label);

private:
  // Private helper functions and data members.
  // Add all private methods as needed, based on implementation in .cpp.
  SlangTU stu;
  FunctionDecl *FD; // The active function decl being processed
  ASTContext *Ctx;
  SmallVectorImpl<char> *charSv;

}; // class SpirGen{};

} // namespace slang