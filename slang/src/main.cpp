//===----------------------------------------------------------------------===//
//  MIT License.
//  Copyright (c) 2020-2026 The SLANG Authors.
//
//  Author: Anshuman Dhuliya (dhuliya@cse.iitb.ac.in, anshumandhuliya@gmail.com)
//
//===----------------------------------------------------------------------===//
// The slang tool with main() method.
//===----------------------------------------------------------------------===//

// Example invocation:
// ./slang test_prog_00.c -p compile_commands.json


#include "main.h"
#include "spir.pb.h"
#include "util.h"
#include "clang/AST/Type.h"

// Generate the SPAN IR from Clang AST.

#define K_00_GLBL_INIT_FUNC_NAME "f:00_glbl_init:optional,comma,separated,flags"
#define K_00_GLBL_INIT_FUNC_ID 1
#define K_00_INT32_TYPE_EID 0
#define OK 0
#define ERR(X) (X)

static llvm::cl::OptionCategory SlangOptions("slang options");

static llvm::cl::opt<std::string> OptOutputDir(
    "out-dir",
    llvm::cl::desc(
        "Specify output directory for output (current dir by default)."
        " The .spir.pb/.spir.py extension is automatically added to each output file."),
    llvm::cl::value_desc("directory"), llvm::cl::cat(SlangOptions));

// Command line option for protobuf output
static llvm::cl::opt<bool> OptProtoOutputKnob(
    "bit-spir",
    llvm::cl::desc("Output SPAN IR in protobuf format (default: true)"),
    llvm::cl::init(true), llvm::cl::cat(SlangOptions));

// Command line option for Python SPAN IR output
static llvm::cl::opt<bool> OptPySpanIrOutputKnob(
    "py-spir",
    llvm::cl::desc("Output SPAN IR in Python format (default: false)"),
    llvm::cl::init(false), llvm::cl::cat(SlangOptions));

void slang::SlangRecord::genMemberAccessExpr(std::string &of, std::string &loc,
                                             int index, SlangExpr &slangExpr) {
  std::stringstream ss;

  ss << "expr.MemberE(\"" << getMemberName(index) << "\"";
  ss << ", " << of;
  ss << ", " << loc << ")"; // end expr.MemberE(

  slangExpr.expr = ss.str();
  slangExpr.qualType = members[index].type;
} // slang::SlangRecord::genMemberAccessExpr()

std::string
slang::SlangRecord::genMemberExpr(std::vector<uint32_t> indexVector) {
  std::stringstream ss;

  std::vector<std::string> members;
  SlangRecord *currentRecord = this;
  llvm::errs() << "\n------------------------\n"
               << currentRecord->members.size() << "\n";
  llvm::errs() << "\n------------------------\n" << indexVector.size() << "\n";
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
} // slang::SlangRecord::genMemberExpr()

std::string slang::SlangRecord::toString() {
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
} // slang::SlangRecord::toString()

std::string slang::SlangRecord::toShortString() {
  std::stringstream ss;

  if (recordKind == Struct) {
    ss << "types.Struct";
  } else {
    ss << "types.Union";
  }
  ss << "(\"" << name << "\")";

  return ss.str();
} // slang::SlangRecord::toShortString()

void slang::SlangTU::addStmt(std::string spanStmt) {
  if (isStaticLocal) {
    auto func = &funcMap[K_00_GLBL_INIT_FUNC_ID];
    func->spanStmts.push_back(spanStmt);
  } else {
    currFunc->spanStmts.push_back(spanStmt);
  }
}

// Save the instruction in the global or the current function.
// Global and function static declarations can be broken into temporary
// assignments; in such cases the instruction must be added to the global
// function.
void slang::SlangTU::addStmtBit(spir::BitInsn *bitInsn) {
  if (isStaticLocal) {
    // Function 1 is a special function that contains initialization of all globals.
    bittu.mutable_functions(K_00_GLBL_INIT_FUNC_ID)->mutable_insns()->AddAllocated(bitInsn);
  } else {
    currBitFunc->mutable_insns()->AddAllocated(bitInsn);
  }
}

bool slang::SlangTU::isBasicBitType(spir::BitDataType *bitDataType) {
  return (bitDataType->vkind() == spir::K_VK::TINT8 ||
          bitDataType->vkind() == spir::K_VK::TINT16 ||
          bitDataType->vkind() == spir::K_VK::TINT32 ||
          bitDataType->vkind() == spir::K_VK::TINT64 ||
          bitDataType->vkind() == spir::K_VK::TUINT8 ||
          bitDataType->vkind() == spir::K_VK::TUINT16 ||
          bitDataType->vkind() == spir::K_VK::TUINT32 ||
          bitDataType->vkind() == spir::K_VK::TUINT64 ||
          bitDataType->vkind() == spir::K_VK::TFLOAT16 ||
          bitDataType->vkind() == spir::K_VK::TFLOAT32 ||
          bitDataType->vkind() == spir::K_VK::TFLOAT64 ||
          bitDataType->vkind() == spir::K_VK::TVOID ||
          bitDataType->vkind() == spir::K_VK::TBOOL);
}

// Add the given entity id and (move) its entity info to the TU.
void slang::SlangTU::moveAndAddBitEntityInfo(uint64_t eid,
                                             spir::BitEntityInfo &bitEntityInfo) {
  // STEP 1: Assert that the entity ID does not already exist
  if (bittu.entityinfo().find(eid) != bittu.entityinfo().end()) {
    std::stringstream ss;
    ss << "Entity ID " << eid << " already exists in BitTU";
    throw std::runtime_error(ss.str());
  }
  // STEP 2: Add a name to eid mapping.
  if (!bitEntityInfo.strval().empty()) {
    bittu.mutable_namestoids()->emplace(bitEntityInfo.strval(), eid);
  }
  // STEP 3: Move the entity info object to the 'eid -> EntityInfo' map.
  bittu.mutable_entityinfo()->emplace(eid, std::move(bitEntityInfo));
}


// BOUND START: dump_routines

// Function to get output filename or error out
std::string slang::SlangTU::getOutFilename(std::string suffix) {
  // If output directory is specified, use it, otherwise use current directory
  std::string outDir = OptOutputDir.empty() ? std::string(".") : OptOutputDir;

  // Build full path by combining output directory, tuName and suffix
  std::string fullPath = outDir + "/" + tuName + suffix;

  SLANG_INFO("Outputting to: " << fullPath)

  return fullPath;
}

// dump entire span ir module for the translation unit.
void slang::SlangTU::dumpSlangIr() {
  // Write the bit translation unit to a file
  if (OptProtoOutputKnob) {
    writeProtoToFile(bittu, getOutFilename(".spir.pb"));
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
    slang::Util::writeToFile(getOutFilename(".spir.py"), ss.str());
  } else {
    SLANG_INFO("FILE_HAS_NO_FUNCTION: Hence no output spanir file.")
  }
} // dumpSlangIr()

void slang::SlangTU::dumpHeader(std::stringstream &ss) {
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

void slang::SlangTU::dumpFooter(std::stringstream &ss) {
  ss << ") # tunit.TranslationUnit() ends\n";
  ss << "\n# END  : A_SPAN_translation_unit!\n";
} // dumpFooter()

void slang::SlangTU::dumpVariables(std::stringstream &ss) {
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

void slang::SlangTU::dumpGlobalInits(std::stringstream &ss) {
  SlangFunc slangFunc = funcMap[K_00_GLBL_INIT_FUNC_ID];
  // ss << "\n";
  ss << NBSP2 << "globalInits = [\n";
  for (auto insn : slangFunc.spanStmts) {
    ss << NBSP4 << insn << ",\n";
  }
  ss << NBSP2 << "], # end globalInits.\n\n";
}

void slang::SlangTU::dumpObjs(std::stringstream &ss) {
  dumpRecords(ss);
  dumpFunctions(ss);
}

void slang::SlangTU::dumpRecords(std::stringstream &ss) {
  ss << NBSP2 << "allRecords = {\n";
  for (auto slangRecord : recordMap) {
    ss << NBSP4;
    ss << "\"" << slangRecord.second.name << "\":\n";
    ss << slangRecord.second.toString();
    ss << ",\n\n";
  }
  ss << NBSP2 << "}, # end allRecords dict\n\n";
}

void slang::SlangTU::dumpFunctions(std::stringstream &ss) {
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

void slang::SlangTU::writeProtoToFile(const spir::BitTU &bittu,
                                      const std::string &filename) {
  std::ofstream output(filename, std::ios::binary);
  if (!output) {
    std::cerr << EXEC_NAME ": Failed to open " << filename << " for writing."
              << std::endl;
    return;
  }
  if (!bittu.SerializeToOstream(&output)) {
    std::cerr << EXEC_NAME ": Failed to write protobuf message to " << filename
              << std::endl;
  }
}

// BOUND END  : dump_routines

slang::SlangBitExpr slang::SpirGen::genMemberAccessBitExpr(SlangBitExpr of,
    const MemberExpr *memberExpr, uint64_t recordEid, QualType qt, SrcLoc srcLoc) {
  assert(!of.compound);

  // STEP 1: Get the eid of the memberExpr
  uint64_t fieldEid = (uint64_t)(memberExpr->getMemberDecl());

  // STEP 2: Get the index of the field in the record.
  int fieldIdx = -1;
  auto itr = std::find(stu.bittu.datatypes().at(recordEid).fopids().begin(),
                   stu.bittu.datatypes().at(recordEid).fopids().end(),
                   fieldEid);
  if (itr != stu.bittu.datatypes().at(recordEid).fopids().end()) {
      fieldIdx = itr - stu.bittu.datatypes().at(recordEid).fopids().begin();
      if (fieldIdx < 0) {
        SLANG_ERROR("Failed to find field index: " << fieldIdx << " for field eid: " << fieldEid);
      }
  } else {
    SLANG_ERROR("Failed to find field eid: " << fieldEid << " in record eid: " << recordEid);
  }

  // STEP 3: Generate the member access bit expression.
  return genMemberAccessBitExpr(of, fieldIdx, recordEid, qt, srcLoc);
} // genMemberAccessBitExpr()

// Similar to a expr.MemberE() expression generator.
slang::SlangBitExpr slang::SpirGen::genMemberAccessBitExpr(SlangBitExpr of,
    int index, uint64_t recordEid, QualType qt, SrcLoc srcLoc) {
  assert(!of.compound);

  std::stringstream ss;

  uint64_t fieldEid = stu.bittu.datatypes().at(recordEid).fopids(index);

  spir::BitEntity be;
  be.set_eid(fieldEid);
  be.set_line(srcLoc.line);
  be.set_col(srcLoc.col);
  return createBinaryBitExpr(of, spir::K_XK::XMEMBER_ACCESS,
     SlangBitExpr(createBitExpr(be)), srcLoc, qt);
} // genMemberAccessBitExpr()

slang::SpirGen::SpirGen(ASTContext *ctx) : Ctx(ctx) {
  stu.uniqLabelCounter = 1;
  stu.uniqIdCounter = 1;
  stu.isStaticLocal = false;
  stu.uniqRecordIdCounter = 1;
  stu.switchCfls = nullptr;

  FD = nullptr;
  charSv = new SmallVector<char, 64>();
  charSv->data()[0] = '\0';
} // SpirGen() constructor

// BOUND START: top_level_routines

void slang::SpirGen::slangInit(const TranslationUnitDecl *TU) {
  // Get the full path from source manager
  std::string fullPath =
      Ctx->getSourceManager()
          .getFileEntryForID(Ctx->getSourceManager().getMainFileID())
          ->tryGetRealPathName()
          .str();

  // Extract the filename and directory from the full path
  size_t lastSlash = fullPath.find_last_of("/\\");
  stu.tuName = fullPath.substr(lastSlash + 1);
  stu.tuDirectory = fullPath.substr(0, lastSlash);

  // Add the name, full path and origin of the TU.
  stu.bittu.set_tuname(stu.tuName);
  stu.bittu.set_abspath(fullPath);
  stu.bittu.set_origin("Clang AST " + clang::getClangFullVersion());

  SLANG_DEBUG("Processing Translation Unit: " << stu.tuName);
  SLANG_DEBUG("Translation Unit Directory: " << stu.tuDirectory);
  SLANG_DEBUG("Translation Unit Full Path: " << fullPath);
}

// It is invoked once for each source translation unit function.
void slang::SpirGen::handleFunctionDecl(FunctionDecl *D) {
  SLANG_EVENT("BOUND START: SLANG_Generated_Output.\n")

  FD = D;
  if (FD) {
    FD = FD->getCanonicalDecl();
    FD = const_cast<FunctionDecl *>(handleFuncNameAndType(FD, true));
    stu.currFunc = &stu.funcMap[(uint64_t)FD];
    SLANG_DEBUG("CurrentFunction: " << stu.currFunc->name << " "
                                    << (uint64_t)FD->getCanonicalDecl())
    if (FD->isVariadic()) {
      SLANG_ERROR("ERROR:VariadicFunction(SkippingBody): "
                  << stu.currFunc->name << " "
                  << (uint64_t)FD->getCanonicalDecl())
    } else {
      handleFunctionBody(FD); // only for non-variadic functions.
    }
  } else {
    SLANG_ERROR("Decl is not a Function")
  }
  stu.clearFunctionSpecificData();
} // handleFunctionDecl()

// invoked when the whole translation unit has been processed
void slang::SpirGen::checkEndOfTranslationUnit(const TranslationUnitDecl *TU) {
  stu.dumpSlangIr();
  SLANG_EVENT("Translation Unit Ended.\n")
  SLANG_EVENT("BOUND END  : SLANG_Generated_Output.\n")
} // checkEndOfTranslationUnit()

// BOUND END  : top_level_routines

// BOUND START: handling_routines

// T can be a Stmt, VarDecl, ValueDecl, or any class that has getBeginLoc()
// method defined.
template <typename T>
slang::SrcLoc slang::SpirGen::getSrcLocBit(const T *decl) {
  slang::SrcLoc loc;

  loc.line = Ctx->getSourceManager().getExpansionLineNumber(decl->getBeginLoc());
  loc.col = Ctx->getSourceManager().getExpansionColumnNumber(decl->getBeginLoc());
  loc.filename = Ctx->getSourceManager().getFilename(decl->getBeginLoc());

  return loc;
} // getSrcLocBit()

// T can be a Stmt, VarDecl, ValueDecl, or any class that has getBeginLoc()
// method defined.
template <typename T>
std::string slang::SpirGen::getLocationString(const T *decl) {
  std::stringstream ss;
  uint32_t line = 0;
  uint32_t col = 0;

  ss << "Info(Loc(";
  line = Ctx->getSourceManager().getExpansionLineNumber(decl->getBeginLoc());
  ss << line << ",";
  col = Ctx->getSourceManager().getExpansionColumnNumber(decl->getBeginLoc());
  ss << col << "))";

  return ss.str();
}

void slang::SpirGen::handleGlobalInits(const TranslationUnitDecl *decl) {
  if (!decl) {
    SLANG_FATAL("TranslationUnitDecl is null");
    return;
  }

  // STEP 1: Initialize the BitTU function for global inits
  // and mark it as the current function.
  spir::BitFunc *bitFunc = stu.bittu.add_functions();
  bitFunc->set_fid(K_00_GLBL_INIT_FUNC_ID);
  bitFunc->set_fname(K_00_GLBL_INIT_FUNC_NAME);
  stu.currBitFunc = bitFunc; // mark the current function being processed

  SlangFunc slangFunc;
  slangFunc.fullName = slangFunc.name = K_00_GLBL_INIT_FUNC_NAME;
  stu.funcMap[K_00_GLBL_INIT_FUNC_ID] = slangFunc;
  stu.currFunc = &stu.funcMap[K_00_GLBL_INIT_FUNC_ID]; // the special global function

  // STEP 2: Iterate over all global variable declarations.
  for (auto it = decl->decls_begin(); it != decl->decls_end(); ++it) {
    const VarDecl *varDecl = dyn_cast<VarDecl>(*it);
    if (varDecl) {
      SLANG_DEBUG("Found global variable: " << varDecl->getNameAsString()
                                            << " at "
                                            << getLocationString(varDecl));
      handleVarDecl(varDecl);
    }
  }
} // handleGlobalInits()

void slang::SpirGen::handleFunctionBody(FunctionDecl *funcDecl) {
  const Stmt *body = funcDecl->getBody();
  if (funcDecl->hasBody()) {
    stu.currFunc->hasBody = true;
    if (OptProtoOutputKnob) {
      convertStmtBit(body);
    } else {
      convertStmt(body);
    }
    SLANG_DEBUG("FunctionHasBody: " << funcDecl->getNameAsString())
  } else {
    // FIXME: control doesn't reach here :(
    stu.currFunc->hasBody = false;
    SLANG_ERROR("No body for function: " << funcDecl->getNameAsString())
  }
} // handleFunctionBody()

// records the function details
const FunctionDecl *
slang::SpirGen::handleFuncNameAndType(const FunctionDecl *funcDecl, bool force) {
  if (OptProtoOutputKnob) {
    return handleFuncNameAndTypeBit(funcDecl, force);
  }

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
    SLANG_DEBUG("AddingFunction: " << slangFunc.name << " "
                                   << (uint64_t)funcDecl << " "
                                   << funcDecl->isDefined() << " "
                                   << (uint64_t)funcDecl->getCanonicalDecl())

    // STEP 1.2: Get function parameters.
    // if (funcDecl->doesThisDeclarationHaveABody())  //&
    // !funcDecl->hasPrototype())
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

// records the function details
const FunctionDecl *
slang::SpirGen::handleFuncNameAndTypeBit(const FunctionDecl *funcDecl, bool force) {
  const FunctionDecl *realFuncDecl = funcDecl;

  // STEP 1.1: Get the definition of the function.
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
    SLANG_DEBUG("AddingFunction: " << slangFunc.name << " "
                                   << (uint64_t)funcDecl << " "
                                   << funcDecl->isDefined() << " "
                                   << (uint64_t)funcDecl->getCanonicalDecl())

    spir::BitFunc *bitFunc = stu.bittu.add_functions();
    bitFunc->set_fid((uint64_t)funcDecl);
    bitFunc->set_fname(slangFunc.fullName);
    bitFunc->set_is_variadic(funcDecl->isVariadic());
    stu.currBitFunc = bitFunc; // mark the current function being processed

    spir::BitEntityInfo beInfo;
    beInfo.set_eid((uint64_t)funcDecl);
    beInfo.set_ekind(spir::K_EK::EFUNC);
    beInfo.set_loc_line(getSrcLocBit(funcDecl).line);
    beInfo.set_loc_col(getSrcLocBit(funcDecl).col);
    beInfo.set_strval(slangFunc.fullName);

    spir::BitDataType bdType;
    bdType.set_typeid_((uint64_t)funcDecl);
    bdType.set_funcprototype(true);
    bdType.set_loc_line(getSrcLocBit(funcDecl).line);
    bdType.set_loc_col(getSrcLocBit(funcDecl).col);
    bdType.set_typename_(slangFunc.fullName);
    stu.bittu.mutable_datatypes()->insert({(uint64_t)funcDecl, std::move(bdType)});

    // STEP 1.2: Get function parameters.
    // if (funcDecl->doesThisDeclarationHaveABody())  //&
    // !funcDecl->hasPrototype())
    if (OptProtoOutputKnob) {
      for (unsigned i = 0, e = funcDecl->getNumParams(); i != e; ++i) {
        const ParmVarDecl *paramVarDecl = funcDecl->getParamDecl(i);
        uint64_t paramEid = (uint64_t)paramVarDecl;
        handleValueDecl(paramVarDecl, slangFunc.name); // adds the var too
        bdType.add_foptypeeids(stu.bittu.entityinfo().at(paramEid).datatypeeid());
        bdType.add_fopids(paramEid);
      }
    } else {
      for (unsigned i = 0, e = funcDecl->getNumParams(); i != e; ++i) {
        const ParmVarDecl *paramVarDecl = funcDecl->getParamDecl(i);
        handleValueDecl(paramVarDecl, slangFunc.name); // adds the var too
        slangFunc.paramNames.push_back(stu.getVar((uint64_t)paramVarDecl).name);
      }
    }
    slangFunc.variadic = funcDecl->isVariadic();

    // STEP 1.3: Get function return type.
    if (OptProtoOutputKnob) {
      MayValue result = convertClangTypeBit(funcDecl->getReturnType());
      if (result.errorCode) {
        SLANG_ERROR("ERROR: Failed to convert function return type: "
                    << funcDecl->getNameAsString()
                    << " Error code: " << result.errorCode)
        return nullptr;
      }
      bdType.set_vkind(stu.bittu.datatypes().at(result.value).vkind());
      bdType.set_subtypeeid(result.value);
    } else {
      slangFunc.retType = convertClangType(funcDecl->getReturnType());
    }

    // STEP 2: Copy the function to the map.
    stu.funcMap[(uint64_t)funcDecl] = slangFunc;

    stu.bittu.mutable_entityinfo()->insert({(uint64_t)funcDecl, beInfo});
    stu.bittu.mutable_datatypes()->insert({(uint64_t)funcDecl, bdType});
    stu.bittu.mutable_namestoids()->insert({slangFunc.fullName, (uint64_t)funcDecl});
  }

  return realFuncDecl;
} // handleFuncNameAndTypeBit()

// All variable declarations are handled here.
int slang::SpirGen::handleVarDecl(const VarDecl *varDecl, std::string funcName) {
  uint64_t varAddr = (uint64_t)varDecl;
  std::string varName;

  stu.isStaticLocal = varDecl->isStaticLocal();

  if (stu.isNewVar(varAddr)) {
    // If here, we are seeing the variable for the first time.
    SlangVar slangVar{};
    slangVar.id = varAddr;
    varName = varDecl->getNameAsString();

    if (OptPySpanIrOutputKnob) {
      slangVar.typeStr = convertClangType(varDecl->getType());
    }

    // Create spir::BitDataType for the variable and store in BitTU
    slang::MayValue result = convertClangTypeBit(varDecl->getType());
    if (result.errorCode) {
      SLANG_ERROR("ERROR: Failed to convert variable type: "
                  << varDecl->getNameAsString()
                  << " Error code: " << result.errorCode)
      return 1000 + result.errorCode;
    }

    spir::BitEntityInfo bitEntityInfo;
    bitEntityInfo.set_eid(varAddr);
    bitEntityInfo.set_datatypeeid(result.value);

    SLANG_DEBUG("NEW_VAR: " << slangVar.convertToString())

    if (varName == "") {
      // used only to name anonymous function parameters
      varName = slang::Util::getNextUniqueIdStr() + "param";
    }

    if (varDecl->isStaticLocal()) {
      slangVar.setLocalVarNameStatic(varName, funcName);
      bitEntityInfo.set_ekind(spir::K_EK::EVAR_LOCL_STATIC);

    } else if (varDecl->hasLocalStorage()) {
      slangVar.setLocalVarName(varName, funcName);
      bitEntityInfo.set_ekind(spir::K_EK::EVAR_LOCL);
      if (stu.varCountMap.find(slangVar.name) != stu.varCountMap.end()) {
        uint64_t newVarId = ++stu.varCountMap[slangVar.name];
        slangVar.setLocalVarName(std::to_string(newVarId) + "D" + varName,
                                 funcName);
      } else {
        stu.varCountMap[slangVar.name] = 1;
      }

    } else if (varDecl->hasGlobalStorage()) {
      slangVar.setGlobalVarName(varName);
      bitEntityInfo.set_ekind(spir::K_EK::EVAR_GLBL);

    } else if (varDecl->hasExternalStorage()) {
      // Treat these as global storage by default
      slangVar.setGlobalVarName(varName);
      bitEntityInfo.set_ekind(spir::K_EK::EVAR_GLBL);

    } else {
      SLANG_ERROR("ERROR:Unknown variable storage.")
    }

    stu.addVar(slangVar.id, slangVar);
    bitEntityInfo.set_loc_line(getSrcLocBit(varDecl).line);
    bitEntityInfo.set_loc_col(getSrcLocBit(varDecl).col);
    bitEntityInfo.set_strval(slangVar.name);
    stu.bittu.mutable_namestoids()->insert({slangVar.name, slangVar.id});
    stu.bittu.mutable_entityinfo()->insert(
        {slangVar.id, std::move(bitEntityInfo)});

    if (varDecl->getType()->isArrayType()) {
      auto arrayType = varDecl->getType()->getAsArrayTypeUnsafe();
      if (isa<VariableArrayType>(arrayType)) {
        if (OptPySpanIrOutputKnob) {
          SlangExpr varExpr =
              convertVariable(varDecl, getLocationString(varDecl));
          SlangExpr sizeExpr = convertVarArrayVariable(
              varDecl->getType(), arrayType->getElementType());

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
        }

        if (OptProtoOutputKnob) {
          spir::BitEntity varEntity = convertVarDeclToBitEntity(varDecl);
          SlangBitExpr sizeExpr = convertVarArrayVariableBit(
              varDecl->getType(), arrayType->getElementType());

          SlangBitExpr allocExpr =
              createUnaryBitExpr(spir::K_XK::XALLOC, sizeExpr, getSrcLocBit(varDecl), Ctx->VoidPtrTy);
          SlangBitExpr tmpVoidPtr = convertToTmpBitExpr(allocExpr);

          spir::BitEntity typeEntity = convertClangTypeToBitEntity(
              varDecl->getType(), ::slang::Util::getNextUniqueId());
          SlangBitExpr castExprBit = createBinaryBitExpr(
              tmpVoidPtr, spir::K_XK::XCAST, SlangBitExpr(createBitExpr(typeEntity)), getSrcLocBit(varDecl), varDecl->getType());

          SlangBitExpr lhsExpr;
          lhsExpr.bitExpr = createBitExpr(varEntity);
          addAssignBitInstr(lhsExpr, castExprBit);
        }
      }
    }

    // check if it has a initialization body
    if (varDecl->hasInit()) {
      // yes it has, so initialize it
      if (varDecl->getInit()->getStmtClass() == Stmt::InitListExprClass) {
        SLANG_DEBUG("AggregateInit: " << slangVar.name << " : Not Supported yet (todo)"); //delete this after testing

        if (OptPySpanIrOutputKnob) {
          SLANG_ERROR("ERROR:AggregateInit: Check if the output is correct.")
          varDecl->dump();
          SlangExpr slangExpr = convertSlangVar(slangVar, varDecl);
          convertInitListExprNew(slangExpr,
                                 cast<InitListExpr>(varDecl->getInit()));
        }

        if (OptProtoOutputKnob) {
          SlangBitExpr bExpr = convertSlangVarBit(slangVar.id, varDecl);
          convertInitListExprBit(bExpr, cast<InitListExpr>(varDecl->getInit()));
        }
      } else {
        if (OptPySpanIrOutputKnob) {
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
          ss << ", " << locStr << ")";    // close instr.AssignI(...
          if (varDecl->isStaticLocal()) { // them make a global init
            auto func = &stu.funcMap[K_00_GLBL_INIT_FUNC_ID];
            func->spanStmts.push_back(ss.str());
          } else {
            stu.addStmt(ss.str());
          }
        }

        if (OptProtoOutputKnob) {
          // FIXME: autogenerated -- incomplete
          spir::BitEntity varEntity = convertVarDeclToBitEntity(varDecl);
          SlangBitExpr rhsExpr = convertStmtBit(varDecl->getInit());
          SlangBitExpr lhsExpr;
          lhsExpr.bitExpr = createBitExpr(varEntity);
          addAssignBitInstr(lhsExpr, rhsExpr);
        }
      }
    }
  } // if (stu.isNewVar(varAddr))

  // else: Not a new variable? No need to re-process an already processed variable.

  stu.isStaticLocal = false;
  return 0;
} // handleVarDecl()

// record the variable name and type
void slang::SpirGen::handleValueDecl(const ValueDecl *valueDecl, std::string funcName) {
  if (OptProtoOutputKnob) {
    return handleValueDeclBit(valueDecl, funcName);
  }

  const VarDecl *varDecl = dyn_cast<VarDecl>(valueDecl);

  std::string varName;
  if (varDecl) {
    handleVarDecl(varDecl, funcName);

  } else if (valueDecl->getAsFunction()) {
    handleFuncNameAndType(valueDecl->getAsFunction());

  } else {
    SLANG_ERROR("ValueDecl is not a VarDecl or a FunctionDecl!")
    SLANG_TRACE_GUARD(valueDecl->dump());
  }
} // handleValueDecl()

// record the variable name and type
void slang::SpirGen::handleValueDeclBit(const ValueDecl *valueDecl, std::string funcName) {
  const VarDecl *varDecl = dyn_cast<VarDecl>(valueDecl);

  std::string varName;
  if (varDecl) {
    handleVarDecl(varDecl, funcName);

  } else if (valueDecl->getAsFunction()) {
    handleFuncNameAndType(valueDecl->getAsFunction());

  } else {
    SLANG_ERROR("ValueDecl is not a VarDecl or a FunctionDecl!")
    SLANG_TRACE_GUARD(valueDecl->dump());
  }
} // handleValueDeclBit()

void slang::SpirGen::handleDeclStmt(const DeclStmt *declStmt) {
  SLANG_DEBUG("Set last DeclStmt to DeclStmt at " << (uint64_t)(declStmt));

  for (auto it = declStmt->decl_begin(); it != declStmt->decl_end(); ++it) {
    if (isa<VarDecl>(*it)) {
      handleVarDecl(cast<VarDecl>(*it), stu.currFunc->name);
    }
  }
} // handleDeclStmt()

void slang::SpirGen::handleDeclStmtBit(const DeclStmt *declStmt) {
  SLANG_DEBUG("Set last DeclStmt to DeclStmt at " << (uint64_t)(declStmt));

  for (auto it = declStmt->decl_begin(); it != declStmt->decl_end(); ++it) {
    if (isa<VarDecl>(*it)) {
      handleVarDecl(cast<VarDecl>(*it), stu.currFunc->name);
    }
  }
} // handleDeclStmtBit()

// BOUND END  : handling_routines

// BOUND START: conversion_routines

// stmtconversion
slang::SlangExpr slang::SpirGen::convertStmt(const Stmt *stmt) {
  SlangExpr slangExpr;

  if (!stmt) {
    return slangExpr;
  }

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
    handleDeclStmt(cast<DeclStmt>(stmt));
    break;

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
    return convertUnaryExprOrTypeTraitExpr(
        cast<UnaryExprOrTypeTraitExpr>(stmt));

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

// stmtconversion
slang::SlangBitExpr slang::SpirGen::convertStmtBit(const Stmt *stmt) {
  SlangBitExpr slangBitExpr;

  if (!stmt) {
    return slangBitExpr;
  }

  SLANG_INFO("ConvertingStmt : " << stmt->getStmtClassName() << "\n")
  SLANG_DEBUG_GUARD(stmt->dump(););

  switch (stmt->getStmtClass()) {
  case Stmt::PredefinedExprClass:
    return convertPredefinedExprBit(cast<PredefinedExpr>(stmt));

  case Stmt::StmtExprClass:
    return convertStmtExprBit(cast<StmtExpr>(stmt));

  case Stmt::CaseStmtClass:
    return convertCaseStmtBit(cast<CaseStmt>(stmt));

  case Stmt::DefaultStmtClass:
    return convertDefaultCaseStmtBit(cast<DefaultStmt>(stmt));

  case Stmt::BreakStmtClass:
    return convertBreakStmtBit(cast<BreakStmt>(stmt));

  case Stmt::ContinueStmtClass:
    return convertContinueStmtBit(cast<ContinueStmt>(stmt));

  case Stmt::LabelStmtClass:
    return convertLabelBit(cast<LabelStmt>(stmt));

  case Stmt::UnaryOperatorClass:
    return convertUnaryOperatorBit(cast<UnaryOperator>(stmt));

  case Stmt::IfStmtClass:
    return convertIfStmtBit(cast<IfStmt>(stmt));

  case Stmt::WhileStmtClass:
    return convertWhileStmtBit(cast<WhileStmt>(stmt));

  // case Stmt::DoStmtClass:
  //   return convertDoStmt(cast<DoStmt>(stmt));

  // case Stmt::ForStmtClass:
  //   return convertForStmt(cast<ForStmt>(stmt));

  case Stmt::CompoundAssignOperatorClass:
  case Stmt::BinaryOperatorClass:
    return convertBinaryOperatorBit(cast<BinaryOperator>(stmt));

  case Stmt::ParenExprClass:
    return convertParenExprBit(cast<ParenExpr>(stmt));

  case Stmt::CompoundStmtClass:
    return convertCompoundStmtBit(cast<CompoundStmt>(stmt));

  case Stmt::DeclStmtClass:
    handleDeclStmt(cast<DeclStmt>(stmt));
    break;

  case Stmt::DeclRefExprClass:
    return convertDeclRefExprBit(cast<DeclRefExpr>(stmt));

  // AD case Stmt::ConstantExprClass:
  // AD   return convertConstantExprBit(cast<ConstantExpr>(stmt));

  case Stmt::IntegerLiteralClass:
    return convertIntegerLiteralBit(cast<IntegerLiteral>(stmt));

  // AD case Stmt::CharacterLiteralClass:
  // AD   return convertCharacterLiteralBit(cast<CharacterLiteral>(stmt));

  // AD case Stmt::FloatingLiteralClass:
  // AD   return convertFloatingLiteralBit(cast<FloatingLiteral>(stmt));

  //AD: case Stmt::StringLiteralClass:
  //AD:   return convertStringLiteralBit(cast<StringLiteral>(stmt));

  case Stmt::ImplicitCastExprClass:
    return convertImplicitCastExprBit(cast<ImplicitCastExpr>(stmt));

  case Stmt::ReturnStmtClass:
    return convertReturnStmtBit(cast<ReturnStmt>(stmt));

  case Stmt::SwitchStmtClass:
    return convertSwitchStmtBit(cast<SwitchStmt>(stmt));

  case Stmt::GotoStmtClass:
    return convertGotoStmtBit(cast<GotoStmt>(stmt));

  //AD: case Stmt::CStyleCastExprClass:
  //AD:   return convertCStyleCastExpr(cast<CStyleCastExpr>(stmt));

  //AD: case Stmt::MemberExprClass:
  //AD:   return convertMemberExpr(cast<MemberExpr>(stmt));

  //AD: case Stmt::ArraySubscriptExprClass:
  //AD:   return convertArraySubscriptExpr(cast<ArraySubscriptExpr>(stmt));

  //AD: case Stmt::UnaryExprOrTypeTraitExprClass:
  //AD:   return convertUnaryExprOrTypeTraitExpr(
  //AD:       cast<UnaryExprOrTypeTraitExpr>(stmt));

  //AD: case Stmt::CallExprClass:
  //AD:   return convertCallExpr(cast<CallExpr>(stmt));

  // case Stmt::CaseStmtClass:
  //   // we manually handle case stmt when we handle switch stmt
  //   break;

  case Stmt::NullStmtClass: // just a ";"
    addNopBitInstr(cast<NullStmt>(stmt));
    break;

  default:
    SLANG_ERROR("ERROR:Unhandled_Stmt: " << stmt->getStmtClassName())
    stmt->dump();
    break;
  }

  return slangBitExpr;
} // convertStmtBit()

/*
 * As observer: PredefinedExpr has only a single child expression.
 * `-PredefinedExpr 0x563d8a43fdb8 <col:233> 'const char [23]' lvalue
 * __PRETTY_FUNCTION__
 *   `-StringLiteral 0x563d8a43fd88 <col:233> 'const char [23]' lvalue "int
 * main(int, char **)"
 */
slang::SlangExpr slang::SpirGen::convertPredefinedExpr(const PredefinedExpr *pe) {
  auto it = pe->child_begin();
  return convertStmt(*it);
} // convertPredefinedExpr()

/*
 * As observer: PredefinedExpr has only a single child expression.
 * `-PredefinedExpr 0x563d8a43fdb8 <col:233> 'const char [23]' lvalue
 * __PRETTY_FUNCTION__
 *   `-StringLiteral 0x563d8a43fd88 <col:233> 'const char [23]' lvalue "int
 * main(int, char **)"
 */
slang::SlangBitExpr
slang::SpirGen::convertPredefinedExprBit(const PredefinedExpr *pe) {
  auto it = pe->child_begin();
  return convertStmtBit(*it);
} // convertPredefinedExprBit()

/*
 * StmtExpr - This is the GNU Statement Expression extension: ({int X=4; X;}).
 */
slang::SlangExpr slang::SpirGen::convertStmtExpr(const StmtExpr *stmt) {
  SlangExpr expr;

  for (auto it = stmt->child_begin(); it != stmt->child_end(); ++it) {
    expr = convertStmt(*it);
  }

  return expr; // return the last expression
}

/*
 * StmtExpr - This is the GNU Statement Expression extension: ({int X=4; X;}).
 */
slang::SlangBitExpr slang::SpirGen::convertStmtExprBit(const StmtExpr *stmt) {
  SlangBitExpr bitExpr;

  for (auto it = stmt->child_begin(); it != stmt->child_end(); ++it) {
    bitExpr = convertStmtBit(*it);
  }

  return bitExpr; // return the last expression
}

slang::SlangExpr slang::SpirGen::convertVarArrayVariable(QualType valueType,
                                                  QualType elementType) {
  const Type *elemTypePtr = elementType.getTypePtr();
  const VariableArrayType *varArrayType =
      cast<VariableArrayType>(valueType.getTypePtr()->getAsArrayTypeUnsafe());

  if (elemTypePtr->isArrayType()) {
    // it will definitely be a VarArray Type (since this func is called)
    SlangExpr tmpSubArraySize = convertVarArrayVariable(
        elementType, elemTypePtr->getAsArrayTypeUnsafe()->getElementType());

    SlangExpr thisVarArrSizeExpr =
        convertToTmp(convertStmt(varArrayType->getSizeExpr()));

    SlangExpr sizeOfThisVarArrExpr = convertToTmp(createBinaryExpr(
        thisVarArrSizeExpr, "op.BO_MUL", tmpSubArraySize,
        thisVarArrSizeExpr.locStr, varArrayType->getSizeExpr()->getType()));

    SlangExpr tmpThisArraySize = convertToTmp(sizeOfThisVarArrExpr);
    return tmpThisArraySize;

  } else {
    // a non-array element type
    TypeInfo typeInfo = Ctx->getTypeInfo(elementType);
    uint64_t size = typeInfo.Width / 8;

    SlangExpr thisVarArrSizeExpr =
        convertToTmp(convertStmt(varArrayType->getSizeExpr()));

    SlangExpr sizeOfInnerNonVarArrType;
    std::stringstream ss;
    ss << "expr.LitE(" << size;
    ss << ", " << thisVarArrSizeExpr.locStr << ")";
    sizeOfInnerNonVarArrType.expr = ss.str();
    sizeOfInnerNonVarArrType.qualType = Ctx->UnsignedIntTy;
    sizeOfInnerNonVarArrType.locStr = thisVarArrSizeExpr.locStr;

    SlangExpr sizeOfThisVarArrExpr = convertToTmp(createBinaryExpr(
        thisVarArrSizeExpr, "op.BO_MUL", sizeOfInnerNonVarArrType,
        thisVarArrSizeExpr.locStr, sizeOfInnerNonVarArrType.qualType));

    SlangExpr tmpThisArraySize = convertToTmp(sizeOfThisVarArrExpr);
    return tmpThisArraySize;
  }
} // convertVarArrayVariable()

slang::SlangBitExpr slang::SpirGen::convertVarArrayVariableBit(QualType valueType,
                                                   QualType elementType) {
  const Type *elemTypePtr = elementType.getTypePtr();
  const VariableArrayType *varArrayType =
      cast<VariableArrayType>(valueType.getTypePtr()->getAsArrayTypeUnsafe());

  if (elemTypePtr->isArrayType()) {
    // it will definitely be a VarArray Type (since this func is called)
    SlangBitExpr tmpSubArraySize = convertVarArrayVariableBit(
        elementType, elemTypePtr->getAsArrayTypeUnsafe()->getElementType());

    SlangBitExpr thisVarArrSizeExpr =
        convertToTmpBitExpr(convertStmtBit(varArrayType->getSizeExpr()));

    SlangBitExpr sizeOfThisVarArrExpr = convertToTmpBitExpr(createBinaryBitExpr(
        thisVarArrSizeExpr, spir::K_XK::XMUL, tmpSubArraySize,
        thisVarArrSizeExpr.srcLoc(), varArrayType->getSizeExpr()->getType()), false, true);

    SlangBitExpr tmpThisArraySize = convertToTmpBitExpr(sizeOfThisVarArrExpr, false, true);
    return tmpThisArraySize;

  } else {
    // a non-array element type
    TypeInfo typeInfo = Ctx->getTypeInfo(elementType);
    uint64_t size = typeInfo.Width / 8;

    SlangBitExpr thisVarArrSizeExpr =
        convertToTmpBitExpr(convertStmtBit(varArrayType->getSizeExpr()));

    SlangBitExpr sizeOfInnerNonVarArrType = createLiteralBitExpr_Integer(size, false, thisVarArrSizeExpr.srcLoc());
    sizeOfInnerNonVarArrType.qualType = Ctx->UnsignedIntTy;

    SlangBitExpr sizeOfThisVarArrExpr = convertToTmpBitExpr(createBinaryBitExpr(
        thisVarArrSizeExpr, spir::K_XK::XMUL, sizeOfInnerNonVarArrType,
        thisVarArrSizeExpr.srcLoc(), sizeOfInnerNonVarArrType.qualType), false, true);

    SlangBitExpr tmpThisArraySize = convertToTmpBitExpr(sizeOfThisVarArrExpr, false, true);
    return tmpThisArraySize;
  }
} // convertVarArrayVariableBit()

slang::SlangBitExpr
slang::SpirGen::convertInitListExprBit(SlangBitExpr &lhs, const InitListExpr *initListExpr) {
  uint32_t index = 0;
  SLANG_DEBUG("INIT_LIST_EXPR_NEW dump:");
  SLANG_DEBUG_GUARD(initListExpr->dump(); initListExpr->getType().dump(););

  for (const auto *it = initListExpr->begin(); it != initListExpr->end();
       ++it) {
    const Stmt *stmt = *it;
    // compute the lhs of the assignment
    SlangBitExpr currLhs = genInitLhsBitExpr(lhs, initListExpr->getType(), index);

    if (stmt->getStmtClass() == Stmt::InitListExprClass) {
      // handle sub-init-list here
      auto subInitExpr = cast<InitListExpr>(stmt);
      SlangBitExpr subLhs = convertToTmp2BitExpr(currLhs); //, subInitExpr->getType());
      convertInitListExprBit(subLhs, subInitExpr);
    } else if (stmt->getStmtClass() == Stmt::ImplicitValueInitExprClass) {
      // handle sub-init-list here
      auto subInitExpr = cast<ImplicitValueInitExpr>(stmt);
      SlangBitExpr subLhs = convertToTmp2BitExpr(currLhs); //, subInitExpr->getType());
      convertImplicitValueInitExprBit(subLhs, subInitExpr);
    } else {
      // compute the rhs part
      SlangBitExpr rhs = convertToTmpBitExpr(convertStmtBit(stmt));
      addAssignBitInstr(currLhs, rhs);
    }
    index += 1;
  }

  return SlangBitExpr{};
} // convertInitListExprBit()

slang::SlangBitExpr slang::SpirGen::convertImplicitValueInitExprBit(
    SlangBitExpr &lhs, // SlangVar& slangVar,
    const ImplicitValueInitExpr *initListExpr) {
//TODO  uint32_t index = 0;
//TODO  SLANG_DEBUG("INIT_LIST_EXPR_NEW dump:");
//TODO  initListExpr->dump();
//TODO  initListExpr->getType().dump();
//TODO
//TODO  for (auto it = initListExpr->child_begin(); it != initListExpr->child_end();
//TODO       ++it) {
//TODO    const Stmt *stmt = *it;
//TODO    // compute the lhs of the assignment
//TODO    SlangExpr currLhs = genInitLhsExprNew(lhs, initListExpr->getType(), index);
//TODO
//TODO    if (stmt->getStmtClass() == Stmt::InitListExprClass) {
//TODO      // handle sub-init-list here
//TODO      auto subInitExpr = cast<InitListExpr>(stmt);
//TODO      SlangExpr subLhs = convertToTmp2BitExpr(currLhs); //, subInitExpr->getType());
//TODO      convertInitListExprNew(subLhs, subInitExpr);
//TODO    } else if (stmt->getStmtClass() == Stmt::ImplicitValueInitExprClass) {
//TODO      // handle sub-init-list here
//TODO      auto subInitExpr = cast<ImplicitValueInitExpr>(stmt);
//TODO      SlangExpr subLhs = convertToTmp2BitExpr(currLhs); //, subInitExpr->getType());
//TODO      convertImplicitValueInitExprBit(subLhs, subInitExpr);
//TODO    } else {
//TODO      // compute the rhs part
//TODO      SlangExpr rhs = convertToTmp(convertStmt(stmt));
//TODO      addAssignInstr(currLhs, rhs, getLocationString(stmt));
//TODO    }
//TODO    index += 1;
//TODO  }
//TODO
  return SlangBitExpr{};
} // convertImplicitValueInitExprBit()

slang::SlangExpr
slang::SpirGen::convertInitListExprNew(SlangExpr &lhs, // SlangVar& slangVar,
                                       const InitListExpr *initListExpr) {
  uint32_t index = 0;
  SLANG_DEBUG("INIT_LIST_EXPR_NEW dump:");
  initListExpr->dump();
  initListExpr->getType().dump();

  for (const auto *it = initListExpr->begin(); it != initListExpr->end();
       ++it) {
    const Stmt *stmt = *it;
    // compute the lhs of the assignment
    SlangExpr currLhs = genInitLhsExprNew(lhs, initListExpr->getType(), index);

    if (stmt->getStmtClass() == Stmt::InitListExprClass) {
      // handle sub-init-list here
      auto subInitExpr = cast<InitListExpr>(stmt);
      SlangExpr subLhs = convertToTmp2(currLhs); //, subInitExpr->getType());
      convertInitListExprNew(subLhs, subInitExpr);
    } else if (stmt->getStmtClass() == Stmt::ImplicitValueInitExprClass) {
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

slang::SlangExpr slang::SpirGen::convertImplicitValueInitExpr(
    SlangExpr &lhs, // SlangVar& slangVar,
    const ImplicitValueInitExpr *initListExpr) {
  uint32_t index = 0;
  SLANG_DEBUG("INIT_LIST_EXPR_NEW dump:");
  initListExpr->dump();
  initListExpr->getType().dump();

  for (auto it = initListExpr->child_begin(); it != initListExpr->child_end();
       ++it) {
    const Stmt *stmt = *it;
    // compute the lhs of the assignment
    SlangExpr currLhs = genInitLhsExprNew(lhs, initListExpr->getType(), index);

    if (stmt->getStmtClass() == Stmt::InitListExprClass) {
      // handle sub-init-list here
      auto subInitExpr = cast<InitListExpr>(stmt);
      SlangExpr subLhs = convertToTmp2(currLhs); //, subInitExpr->getType());
      convertInitListExprNew(subLhs, subInitExpr);
    } else if (stmt->getStmtClass() == Stmt::ImplicitValueInitExprClass) {
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
} // convertImplicitValueInitExpr()

slang::SlangExpr slang::SpirGen::convertInitListExpr(
    SlangVar &slangVar, const InitListExpr *initListExpr,
    const VarDecl *varDecl, std::vector<uint32_t> &indexVector,
    bool staticLocal) {
  uint32_t index = 0;
  SLANG_DEBUG("INIT_LIST_EXPR dump:");
  initListExpr->dump();
  initListExpr->getType().dump();
  for (auto it = initListExpr->begin(); it != initListExpr->end(); ++it) {
    const Stmt *stmt = *it;
    if (stmt->getStmtClass() == Stmt::InitListExprClass) {
      // && isCompoundTypeAt(varDecl, indexVector))
      indexVector.push_back(index);
      convertInitListExpr(slangVar, cast<InitListExpr>(stmt), varDecl,
                          indexVector, staticLocal);
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
bool slang::SpirGen::isCompoundTypeAt(const VarDecl *varDecl,
                                      std::vector<int> &indexVector) {
  // TODO
  return true;
}

slang::SlangBitExpr
slang::SpirGen::genInitLhsBitExpr(SlangBitExpr lhs, QualType initExprListQt, int index) {
  SlangBitExpr slangExpr;

  const auto *type = initExprListQt.getTypePtr();

  if (type->isArrayType()) {
    SlangBitExpr indexExpr = createLiteralBitExpr_Integer(index, false, lhs.srcLoc());
    slangExpr = createBinaryBitExpr(lhs, spir::K_XK::XARR_INDX,
        indexExpr, lhs.srcLoc(), type->getAsArrayTypeUnsafe()->getElementType());

  } else {
    // must be a record type
    const RecordDecl *recordDecl;

    if (type->isStructureType()) {
      recordDecl = type->getAsStructureType()->getDecl();
    } else { // must be a union then
      recordDecl = type->getAsUnionType()->getDecl();
    }

    //TODO: complete the function
    auto slangRecord = stu.getRecord((uint64_t)recordDecl);
    //TODO slangRecord.genMemberAccessExpr(lhs.expr, lhs.locStr, index, slangExpr);
  }

  slangExpr.compound = true;
  slangExpr.bitExpr->set_loc_line(lhs.srcLoc().line);
  slangExpr.bitExpr->set_loc_col(lhs.srcLoc().col);
  return SlangBitExpr{};
} // genInitLhsBitExpr()

slang::SlangExpr
slang::SpirGen::genInitLhsExprNew(SlangExpr &lhs, // SlangVar& slangVar,
                                  QualType initExprListQt, int index) {
  SlangExpr slangExpr;
  std::stringstream ss;

  const auto *type = initExprListQt.getTypePtr();

  std::string prefix = "";
  if (type->isArrayType()) {
    ss << prefix << "expr.ArrayE(";
    ss << "expr.LitE(" << index << ", " << lhs.locStr << ")";
    ss << ", " << lhs.expr;          // must be a variable expr only
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
slang::SlangExpr slang::SpirGen::genInitLhsExpr(SlangVar &slangVar,
                                         const VarDecl *varDecl,
                                         std::vector<uint32_t> &indexVector) {
  SlangExpr slangExpr;
  std::stringstream ss;

  std::string prefix = "";
  if (varDecl->getType()->isArrayType()) {
    for (auto it = indexVector.end() - 1; it != indexVector.begin() - 1; --it) {
      ss << prefix << "expr.ArrayE(" << "expr.LitE(" << *it << ", "
         << getLocationString(varDecl) << ")";
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
slang::SlangExpr slang::SpirGen::convertBinaryCommaOp(const BinaryOperator *binOp) {
  auto it = binOp->child_begin();
  const Stmt *leftOprnd = *it;
  ++it;
  const Stmt *rightOprnd = *it;

  convertStmt(leftOprnd);

  SlangExpr rightExpr = convertToTmp(convertStmt(rightOprnd));

  return rightExpr;
} // convertBinaryCommaOp()

// guaranteed to be a comma operator
slang::SlangBitExpr
slang::SpirGen::convertBinaryCommaOpBit(const BinaryOperator *binOp) {
  auto it = binOp->child_begin();
  const Stmt *leftOprnd = *it;
  ++it;
  const Stmt *rightOprnd = *it;

  convertStmtBit(leftOprnd);

  SlangBitExpr rightExpr =
      convertToTmpBitExpr(convertStmtBit(rightOprnd), false, true);

  return rightExpr;
} // convertBinaryCommaOpBit()

slang::SlangExpr slang::SpirGen::convertCallExpr(const CallExpr *callExpr) {
  SlangExpr slangExpr;

  auto it = callExpr->child_begin();

  const Stmt *callee = *it;
  SlangExpr calleeExpr = convertToTmp(convertStmt(callee));

  std::vector<const Stmt *> args;
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

  ss << ", " << getLocationString(callExpr) << ")"; // close expr.CallE(...

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

bool slang::SpirGen::hasVoidReturnType(const CallExpr *callExpr) {
  QualType qt = callExpr->getType();
  if (qt.isNull()) {
    return true;
  }

  qt = getCleanedQualType(qt);
  const Type *type = qt.getTypePtr();
  return type->isVoidType();
} // hasVoidReturnType()

slang::SlangExpr
slang::SpirGen::convertArraySubscriptExpr(const ArraySubscriptExpr *arrayExpr) {
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

slang::SlangBitExpr slang::SpirGen::convertMemberExprBit(const MemberExpr *memberExpr) {
  auto it = memberExpr->child_begin();
  const Stmt *child = *it;
  SlangBitExpr parentExpr = convertStmtBit(child);
  SlangBitExpr parentTmpExpr;
  SlangBitExpr memSlangExpr;
  uint64_t recordTypeEid = 0;
  std::stringstream ss;

  // STEP 1: Get the id of the parent record type
  auto recordQt = parentExpr.qualType;
  if (parentExpr.qualType.getTypePtr()->isPointerType()) {
    recordQt = parentExpr.qualType.getTypePtr()->getPointeeType();
  }
  auto mayVal = convertClangTypeBit(recordQt);
  if (mayVal.errorCode) {
    SLANG_ERROR("Failed to convert record type: " << mayVal.errorCode);
  }
  recordTypeEid = mayVal.value;

  // STEP 2: Store parent to a temporary if it is a compound expression
  parentTmpExpr = parentExpr;
  if (parentExpr.compound) {
    if (parentExpr.qualType.getTypePtr()->isPointerType()) {
      //|| !(parentExpr.expr.substr(0,12) == "expr.MemberE"))
      parentTmpExpr = convertToTmpBitExpr(parentExpr);
    } else {
      switch (parentExpr.bitExpr->xkind()) {
        case spir::K_XK::XMEMBER_ACCESS:
          parentExpr.bitExpr->set_xkind(spir::K_XK::XMEMBER_ADDROF);
          break;
        case spir::K_XK::XARR_INDX:
          parentExpr.bitExpr->set_xkind(spir::K_XK::XARR_INDX_ADDROF);
          break;
        case spir::K_XK::XVAL:
          parentExpr.bitExpr->set_xkind(spir::K_XK::XADDROF);
          parentExpr.compound = true;
          break;
        default:
          break;
      }  
      parentTmpExpr = convertToTmpBitExpr(parentExpr);
    }
  }

  // STEP 3: Generate the member access bit expression.
  auto expr = genMemberAccessBitExpr(parentTmpExpr, memberExpr, recordTypeEid, memberExpr->getType(), getSrcLocBit(memberExpr));
  return expr;
} // convertMemberExprBit()

slang::SlangExpr slang::SpirGen::convertMemberExpr(const MemberExpr *memberExpr) {
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

slang::SlangExpr slang::SpirGen::convertCStyleCastExpr(const CStyleCastExpr *cCast) {
  auto it = cCast->child_begin();
  QualType qt = cCast->getType();

  return convertCastExpr(*it, qt, getLocationString(cCast));
} // convertCStyleCastExpr()

slang::SlangExpr slang::SpirGen::convertGotoStmt(const GotoStmt *gotoStmt) {
  std::string label = gotoStmt->getLabel()->getNameAsString();
  addGotoInstr(label);
  return SlangExpr{};
} // convertGotoStmt()

slang::SlangBitExpr slang::SpirGen::convertGotoStmtBit(const GotoStmt *gotoStmt) {
  std::string label = gotoStmt->getLabel()->getNameAsString();
  spir::BitEntity labelBit = createLabelBit(label, getSrcLocBit(gotoStmt));
  addGotoInstrBit(labelBit, getSrcLocBit(gotoStmt));
  return SlangBitExpr{};
} // convertGotoStmt()

slang::SlangExpr slang::SpirGen::convertBreakStmt(const BreakStmt *breakStmt) {
  addGotoInstr(stu.peekExitLabel());
  return SlangExpr{};
}

slang::SlangBitExpr slang::SpirGen::convertBreakStmtBit(const BreakStmt *breakStmt) {
  addGotoInstrBit(stu.peekExitLabelBit(), getSrcLocBit(breakStmt));
  return SlangBitExpr{};
}

slang::SlangExpr
slang::SpirGen::convertContinueStmt(const ContinueStmt *continueStmt) {
  addGotoInstr(stu.peekEntryLabel());
  return SlangExpr{};
}

slang::SlangBitExpr
slang::SpirGen::convertContinueStmtBit(const ContinueStmt *continueStmt) {
  addGotoInstrBit(stu.peekEntryLabelBit(), getSrcLocBit(continueStmt));
  return SlangBitExpr{};
}

slang::SlangExpr slang::SpirGen::convertSwitchStmtNew(const SwitchStmt *switchStmt) {
  auto oldSwitchCfls = stu.switchCfls;
  auto switchCfls = SwitchCtrlFlowLabels(stu.genNextLabelCountStr());
  stu.switchCfls = &switchCfls;

  stu.pushLabels(stu.switchCfls->switchStartLabel,
                 stu.switchCfls->switchExitLabel);

  addLabelInstr(stu.switchCfls->switchStartLabel);

  const Expr *condExpr = switchStmt->getCond();
  SlangExpr switchCond = convertToTmp(convertStmt(condExpr));
  stu.switchCfls->switchCond = switchCond;

  // Get all case statements inside switch.
  if (switchStmt->getBody()) {
    convertStmt(switchStmt->getBody());
  } else {
    for (auto it = switchStmt->child_begin(); it != switchStmt->child_end();
         ++it) {
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
  stu.switchCfls = oldSwitchCfls; // restore the old ptr

  stu.popLabel();
  return SlangExpr{};
} // convertSwitchStmtNew()

slang::SlangBitExpr slang::SpirGen::convertSwitchStmtBit(const SwitchStmt *switchStmt) {
  auto oldSwitchCflsBit = stu.switchCflsBit;
  auto switchCflsBit = SwitchCtrlFlowLabelsBit(stu.genNextLabelCountStr());
  stu.switchCflsBit = &switchCflsBit;

  auto switchStartLabelBit = createLabelBit(stu.switchCflsBit->switchStartLabel, getSrcLocBit(switchStmt));
  auto switchExitLabelBit = createLabelBit(stu.switchCflsBit->switchExitLabel, getSrcLocBit(switchStmt));
  stu.pushLabelsBit(switchStartLabelBit, switchExitLabelBit);

  addLabelInstrBit(switchStartLabelBit, getSrcLocBit(switchStmt));

  const Expr *condExpr = switchStmt->getCond();
  SlangBitExpr switchCond = convertToIfTmpBit(convertStmtBit(condExpr));
  stu.switchCflsBit->switchCond = switchCond;

  // Get all case statements inside switch.
  if (switchStmt->getBody()) {
    convertStmtBit(switchStmt->getBody());
  } else {
    for (auto it = switchStmt->child_begin(); it != switchStmt->child_end();
         ++it) {
      convertStmtBit(*it);
    }
  }

  auto gotoBodyLabelBit = createLabelBit(stu.switchCflsBit->nextBodyLabel, getSrcLocBit(switchStmt));
  auto nextCaseCondLabelBit = createLabelBit(stu.switchCflsBit->nextCaseCondLabel, getSrcLocBit(switchStmt));
  auto defaultCaseLabelBit = createLabelBit(stu.switchCflsBit->defaultCaseLabel, getSrcLocBit(switchStmt));
  addGotoInstrBit(gotoBodyLabelBit, getSrcLocBit(switchStmt));
  addLabelInstrBit(nextCaseCondLabelBit, getSrcLocBit(switchStmt)); // the last condition label
  if (stu.switchCflsBit->defaultExists) {
    addGotoInstrBit(defaultCaseLabelBit, getSrcLocBit(switchStmt));
  }
  addLabelInstrBit(gotoBodyLabelBit, getSrcLocBit(switchStmt));
  addLabelInstrBit(switchExitLabelBit, getSrcLocBit(switchStmt));
  stu.switchCflsBit = oldSwitchCflsBit; // restore the old ptr

  stu.popLabelBit();
  return SlangBitExpr{};
} // convertSwitchStmtBit()

slang::SlangExpr slang::SpirGen::convertCaseStmt(const CaseStmt *caseStmt) {
  if (stu.switchCfls->thisCaseCondLabel != "") {
    addGotoInstr(
        stu.switchCfls->nextBodyLabel); // add a fall through for prev body
  }

  stu.switchCfls->setupForThisCase();

  const Stmt *cond = *(caseStmt->child_begin());
  SlangExpr caseCond = convertToTmp(convertStmt(cond));

  addLabelInstr(stu.switchCfls->thisCaseCondLabel); // condition label
  // add the actual condition
  SlangExpr eqExpr = convertToIfTmp(
      createBinaryExpr(stu.switchCfls->switchCond, "op.BO_EQ", caseCond,
                       getLocationString(caseStmt), Ctx->UnsignedIntTy));
  addCondInstr(eqExpr.expr, stu.switchCfls->thisBodyLabel,
               stu.switchCfls->nextCaseCondLabel, getLocationString(caseStmt));

  // case body
  if (stu.switchCfls->gotoLabel != "") {
    std::stringstream ss;
    ss << "instr.LabelI(\"" << stu.switchCfls->gotoLabel << "\"";
    ss << ", " << stu.switchCfls->gotoLabelLocStr
       << ")"; // close instr.LabelI(...
    stu.addStmt(ss.str());
    stu.switchCfls->gotoLabel = stu.switchCfls->gotoLabelLocStr = "";
  }
  addLabelInstr(stu.switchCfls->thisBodyLabel);
  for (auto it = caseStmt->child_begin(); it != caseStmt->child_end(); ++it) {
    convertStmt(*it);
  }

  return SlangExpr{};
} // convertCaseStmt()

slang::SlangBitExpr slang::SpirGen::convertCaseStmtBit(const CaseStmt *caseStmt) {
  if (stu.switchCflsBit->thisCaseCondLabel != "") {
    auto gotoBodyLabelBit = createLabelBit(stu.switchCflsBit->nextBodyLabel, getSrcLocBit(caseStmt));
    addGotoInstrBit(gotoBodyLabelBit, getSrcLocBit(caseStmt)); // add a fall through for prev body
  }

  stu.switchCflsBit->setupForThisCase();

  const Stmt *cond = *(caseStmt->child_begin());
  SlangBitExpr caseCond = convertToIfTmpBit(convertStmtBit(cond));

  auto thisCaseCondLabelBit = createLabelBit(stu.switchCflsBit->thisCaseCondLabel, getSrcLocBit(caseStmt));
  addLabelInstrBit(thisCaseCondLabelBit, getSrcLocBit(caseStmt)); // condition label
  // add the actual condition
  SlangBitExpr eqExpr = createBinaryBitExpr(stu.switchCflsBit->switchCond, spir::K_XK::XEQ, caseCond,
                       getSrcLocBit(caseStmt), Ctx->UnsignedIntTy);
  auto nextCaseCondLabelBit = createLabelBit(stu.switchCflsBit->nextCaseCondLabel, getSrcLocBit(caseStmt));
  addCondInstrBit(eqExpr, thisCaseCondLabelBit, nextCaseCondLabelBit, getSrcLocBit(caseStmt));

  // case body
  if (stu.switchCflsBit->gotoLabel != "") {
    auto gotoLabelBit = createLabelBit(stu.switchCflsBit->gotoLabel, getSrcLocBit(caseStmt));
    std::stringstream ss;
    addLabelInstrBit(gotoLabelBit, getSrcLocBit(caseStmt));
    stu.switchCflsBit->gotoLabel = stu.switchCflsBit->gotoLabelLocStr = "";
  }
  auto thisBodyLabelBit = createLabelBit(stu.switchCflsBit->thisBodyLabel, getSrcLocBit(caseStmt));
  addLabelInstrBit(thisBodyLabelBit, getSrcLocBit(caseStmt));
  for (auto it = caseStmt->child_begin(); it != caseStmt->child_end(); ++it) {
    convertStmtBit(*it);
  }

  return SlangBitExpr{};
} // convertCaseStmtBit()

slang::SlangExpr
slang::SpirGen::convertDefaultCaseStmt(const DefaultStmt *defaultStmt) {
  if (stu.switchCfls->thisCaseCondLabel != "") {
    addGotoInstr(
        stu.switchCfls->nextBodyLabel); // add a fall through for prev body
  }

  stu.switchCfls->setupForDefaultCase();

  addLabelInstr(stu.switchCfls->defaultCaseLabel); // default case label

  // default body
  addLabelInstr(stu.switchCfls->thisBodyLabel); // body label
  for (auto it = defaultStmt->child_begin(); it != defaultStmt->child_end();
       ++it) {
    convertStmt(*it);
  }

  return SlangExpr{};
} // convertDefaultCaseStmt()

slang::SlangBitExpr
slang::SpirGen::convertDefaultCaseStmtBit(const DefaultStmt *defaultStmt) {
  if (stu.switchCflsBit->thisCaseCondLabel != "") {
    auto gotoBodyLabelBit = createLabelBit(stu.switchCflsBit->nextBodyLabel, getSrcLocBit(defaultStmt));
    addGotoInstrBit(gotoBodyLabelBit, getSrcLocBit(defaultStmt)); // add a fall through for prev body
  }

  stu.switchCflsBit->setupForDefaultCase();

  auto defaultCaseLabelBit = createLabelBit(stu.switchCflsBit->defaultCaseLabel, getSrcLocBit(defaultStmt));
  addLabelInstrBit(defaultCaseLabelBit, getSrcLocBit(defaultStmt)); // default case label

  // default body
  auto thisBodyLabelBit = createLabelBit(stu.switchCflsBit->thisBodyLabel, getSrcLocBit(defaultStmt));
  addLabelInstrBit(thisBodyLabelBit, getSrcLocBit(defaultStmt)); // body label
  for (auto it = defaultStmt->child_begin(); it != defaultStmt->child_end();
       ++it) {
    convertStmtBit(*it);
  }

  return SlangBitExpr{};
} // convertDefaultCaseStmtBit()

slang::SlangExpr slang::SpirGen::convertSwitchStmt(const SwitchStmt *switchStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string switchStartLabel = id + "SwitchStart";
  std::string switchExitLabel = id + "SwitchExit";
  std::string caseCondLabel = id + "CaseCond" + "-";
  std::string caseBodyLabel = id + "CaseBody" + "-";
  std::string defaultLabel = id + "Default";
  bool defaultLabelAdded = false;

  stu.pushLabels(switchStartLabel, switchExitLabel);

  addLabelInstr(switchStartLabel);

  std::vector<const Stmt *> caseStmtsWithDefault;
  // std::vector<const Stmt*> defaultStmt;

  const Expr *condExpr = switchStmt->getCond();
  SlangExpr switchCond = convertToTmp(convertStmt(condExpr));

  // Get all case statements inside switch.
  if (switchStmt->getBody()) {
    getCaseStmts(caseStmtsWithDefault, switchStmt->getBody());
    // getDefaultStmt(defaultStmt, switchStmt->getBody());

  } else {
    for (auto it = switchStmt->child_begin(); it != switchStmt->child_end();
         ++it) {
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
  for (size_t index = 0; index < caseStmtsWithDefault.size(); ++index) {
    // for (const Stmt *stmt: caseStmtsWithDefault) {
    const Stmt *stmt = caseStmtsWithDefault[index];

    if (isa<CaseStmt>(stmt)) {
      const CaseStmt *caseStmt = cast<CaseStmt>(stmt);
      // find where to jump to if the case condition is false
      std::string falseLabel;
      falseLabel = defaultLabel;

      if (index != totalStmts - 1) {
        // try jumping to the next case's cond
        for (size_t i = index + 1; i < totalStmts; ++i) {
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
      SlangExpr eqExpr = convertToIfTmp(
          createBinaryExpr(switchCond, "op.BO_EQ", caseCond,
                           getLocationString(caseStmt), Ctx->UnsignedIntTy));
      addCondInstr(eqExpr.expr, bodyLabel, falseLabel,
                   getLocationString(caseStmt));

      // case body
      addLabelInstr(bodyLabel);
      for (auto it = caseStmt->child_begin(); it != caseStmt->child_end();
           ++it) {
        convertStmt(*it);
      }

      // if it has break, then jump to exit
      // Note: a break as child stmt is covered recursively
      if (caseOrDefaultStmtHasSiblingBreak(caseStmt)) {
        addGotoInstr(switchExitLabel);
      } else {
        // try jumping to the next case's body if present :)
        if (index != totalStmts - 1) {
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
      for (auto it = stmt->child_begin(); it != stmt->child_end(); ++it) {
        convertStmt(*it);
      }

      // if it has break, then jump to exit
      // Note: a break as child stmt is covered recursively
      if (caseOrDefaultStmtHasSiblingBreak(stmt)) {
        addGotoInstr(switchExitLabel);
      } else {
        // try jumping to the next case's body
        if (index != totalStmts - 1) {
          // must be a case stmt, since this is a default stmt :)
          ss << caseBodyLabel << index + 1;
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
bool slang::SpirGen::caseOrDefaultStmtHasSiblingBreak(const Stmt *stmt) {
  const auto &parents = Ctx->getParents(DynTypedNode::create(*stmt));

  const Stmt *parentStmt = parents[0].get<Stmt>();
  bool lastStmtWasTheGivenCaseOrDefaultStmt = false;
  bool hasBreak = false;

  for (auto it = parentStmt->child_begin(); it != parentStmt->child_end();
       ++it) {
    if (!*it) {
      continue;
    }

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
bool slang::SpirGen::isIncompleteType(const Type *type) {
  bool retVal = false;

  if (type->isIncompleteArrayType() || type->isVariableArrayType()) {
    retVal = true;
  }
  return retVal;
}

// get all case statements recursively (case stmts can be hierarchical)
void slang::SpirGen::getCaseStmts(
    std::vector<const Stmt *> &caseStmtsWithDefault, const Stmt *stmt) {
  if (!stmt)
    return;

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
    for (auto it = compoundStmt->body_begin(); it != compoundStmt->body_end();
         ++it) {
      getCaseStmts(caseStmtsWithDefault, (*it));
    }
  } else if (isa<SwitchStmt>(stmt)) {
    // do nothing, as it will be handled separately

  } else if (isa<DefaultStmt>(stmt)) {
    auto defaultStmt = cast<DefaultStmt>(stmt);
    caseStmtsWithDefault.push_back(stmt);
    for (auto it = defaultStmt->child_begin(); it != defaultStmt->child_end();
         ++it) {
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
void slang::SpirGen::getDefaultStmt(std::vector<const Stmt *> &defaultStmt,
                                    const Stmt *stmt) {
  if (!stmt)
    return;

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
    for (auto it = compoundStmt->body_begin(); it != compoundStmt->body_end();
         ++it) {
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

slang::SlangExpr slang::SpirGen::convertReturnStmt(const ReturnStmt *returnStmt) {
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

slang::SlangBitExpr
slang::SpirGen::convertReturnStmtBit(const ReturnStmt *returnStmt) {
  const Expr *retVal = returnStmt->getRetValue();

  SlangBitExpr retExpr = convertToTmpBitExpr(convertStmtBit(retVal), false, true);

  spir::BitInsn *insn = new spir::BitInsn();
  SrcLoc srcLoc = getSrcLocBit(returnStmt);
  insn->set_ikind(::spir::K_IK::IRETURN);
  insn->set_allocated_expr1(retExpr.bitExpr);
  insn->set_loc_line(srcLoc.line);
  insn->set_loc_col(srcLoc.col);

  stu.addStmtBit(insn);

  // Return empty expression, assuming no one needs it.
  return SlangBitExpr{};
} // convertReturnStmtBit()

slang::SlangExpr
slang::SpirGen::convertConditionalOp(const ConditionalOperator *condOp) {
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

slang::SlangBitExpr
slang::SpirGen::convertConditionalOpBit(const ConditionalOperator *condOp) {
  SlangBitExpr cond = convertToTmpBitExpr(convertStmtBit(condOp->getCond()), false, true);
  SlangBitExpr trueExpr = convertToTmpBitExpr(convertStmtBit(condOp->getTrueExpr()), false, true);
  SlangBitExpr falseExpr = convertToTmpBitExpr(convertStmtBit(condOp->getFalseExpr()), false, true);
  SlangBitExpr tmpVar = SlangBitExpr(createBitExpr(
    genTmpBitEntity(spir::K_VK::TNIL, "t", getSrcLocBit(condOp), trueExpr.qualType)));

  std::string id = stu.genNextLabelCountStr();
  std::string ifTrueLabel = id + "CondOpTrue";
  std::string ifFalseLabel = id + "CondOpFalse";
  std::string ifExitLabel = id + "CondOpExit";
  
  spir::BitEntity ifTrueLabelBit = createLabelBit(ifTrueLabel, getSrcLocBit(condOp));
  spir::BitEntity ifFalseLabelBit = createLabelBit(ifFalseLabel, getSrcLocBit(condOp));
  spir::BitEntity ifExitLabelBit = createLabelBit(ifExitLabel, getSrcLocBit(condOp));

  addCondInstrBit(cond, ifTrueLabelBit, ifFalseLabelBit, getSrcLocBit(condOp));

  addLabelInstrBit(ifTrueLabelBit, getSrcLocBit(condOp));
  addAssignBitInstr(tmpVar, trueExpr);

  addGotoInstrBit(ifExitLabelBit, getSrcLocBit(condOp));
  addLabelInstrBit(ifFalseLabelBit, getSrcLocBit(condOp));

  addAssignBitInstr(tmpVar, falseExpr);

  addLabelInstrBit(ifExitLabelBit, getSrcLocBit(condOp));

  return tmpVar;
} // convertConditionalOpBit()

slang::SlangExpr slang::SpirGen::convertIfStmt(const IfStmt *ifStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string ifTrueLabel = id + "IfTrue";
  std::string ifFalseLabel = id + "IfFalse";
  std::string ifExitLabel = id + "IfExit";

  const Stmt *condition = ifStmt->getCond();
  SlangExpr conditionExpr = convertStmt(condition);
  conditionExpr = convertToIfTmp(conditionExpr);

  addCondInstr(conditionExpr.expr, ifTrueLabel, ifFalseLabel,
               getLocationString(ifStmt));

  addLabelInstr(ifTrueLabel);

  const Stmt *body = ifStmt->getThen();
  if (body) {
    convertStmt(body);
  }

  addGotoInstr(ifExitLabel);
  addLabelInstr(ifFalseLabel);

  const Stmt *elseBody = ifStmt->getElse();
  if (elseBody) {
    convertStmt(elseBody);
  }

  addLabelInstr(ifExitLabel);

  return SlangExpr{}; // return empty expression
} // convertIfStmt()

slang::SlangBitExpr slang::SpirGen::convertIfStmtBit(const IfStmt *ifStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string ifTrueLabel = id + "IfTrue";
  std::string ifFalseLabel = id + "IfFalse";
  std::string ifExitLabel = id + "IfExit";
  
  spir::BitEntity ifTrueLabelBit = createLabelBit(ifTrueLabel, getSrcLocBit(ifStmt));
  spir::BitEntity ifFalseLabelBit = createLabelBit(ifFalseLabel, getSrcLocBit(ifStmt));
  spir::BitEntity ifExitLabelBit = createLabelBit(ifExitLabel, getSrcLocBit(ifStmt));

  const Stmt *condition = ifStmt->getCond();
  SlangBitExpr conditionExpr = convertStmtBit(condition);
  conditionExpr = convertToIfTmpBit(conditionExpr);

  SLANG_PRINT("here1: \n" << conditionExpr.toString());
  addCondInstrBit(conditionExpr, ifTrueLabelBit, ifFalseLabelBit, getSrcLocBit(ifStmt));

  SLANG_PRINT("here2");
  addLabelInstrBit(ifTrueLabelBit, getSrcLocBit(ifStmt));

  const Stmt *body = ifStmt->getThen();
  if (body) {
    convertStmtBit(body);
  }

  addGotoInstrBit(ifExitLabelBit, getSrcLocBit(ifStmt));
  addLabelInstrBit(ifFalseLabelBit, getSrcLocBit(ifStmt));

  const Stmt *elseBody = ifStmt->getElse();
  if (elseBody) {
    convertStmtBit(elseBody);
  }

  addLabelInstrBit(ifExitLabelBit, getSrcLocBit(ifStmt));

  return SlangBitExpr{}; // return empty expression
} // convertIfStmtBit()

slang::SlangExpr slang::SpirGen::convertWhileStmt(const WhileStmt *whileStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string whileCondLabel = id + "WhileCond";
  std::string whileBodyLabel = id + "WhileBody";
  std::string whileExitLabel = id + "WhileExit";

  stu.pushLabels(whileCondLabel, whileExitLabel);

  addLabelInstr(whileCondLabel);

  const Stmt *condition = whileStmt->getCond();
  SlangExpr conditionExpr = convertStmt(condition);
  conditionExpr = convertToIfTmp(conditionExpr);

  addCondInstr(conditionExpr.expr, whileBodyLabel, whileExitLabel,
               getLocationString(condition));

  addLabelInstr(whileBodyLabel);

  const Stmt *body = whileStmt->getBody();
  if (body) {
    convertStmt(body);
  }

  // unconditional jump to startConditionLabel
  addGotoInstr(whileCondLabel);

  addLabelInstr(whileExitLabel);

  stu.popLabel();
  return SlangExpr{}; // return empty expression
} // convertWhileStmt()

slang::SlangBitExpr slang::SpirGen::convertWhileStmtBit(const WhileStmt *whileStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string whileCondLabel = id + "WhileCond";
  std::string whileBodyLabel = id + "WhileBody";
  std::string whileExitLabel = id + "WhileExit";

  auto whileCondLabelBit = createLabelBit(whileCondLabel, getSrcLocBit(whileStmt));
  auto whileBodyLabelBit = createLabelBit(whileBodyLabel, getSrcLocBit(whileStmt));
  auto whileExitLabelBit = createLabelBit(whileExitLabel, getSrcLocBit(whileStmt));

  stu.pushLabelsBit(whileCondLabelBit, whileExitLabelBit);

  addLabelInstrBit(whileCondLabelBit, getSrcLocBit(whileStmt));

  const Stmt *condition = whileStmt->getCond();
  SlangBitExpr conditionExpr = convertStmtBit(condition);
  conditionExpr = convertToIfTmpBit(conditionExpr);

  addCondInstrBit(conditionExpr, whileBodyLabelBit, whileExitLabelBit, getSrcLocBit(whileStmt));

  addLabelInstrBit(whileBodyLabelBit, getSrcLocBit(whileStmt));

  const Stmt *body = whileStmt->getBody();
  if (body) {
    convertStmtBit(body);
  }

  // unconditional jump to startConditionLabel
  addGotoInstrBit(whileCondLabelBit, getSrcLocBit(whileStmt));

  addLabelInstrBit(whileExitLabelBit, getSrcLocBit(whileStmt));

  stu.popLabelBit();
  return SlangBitExpr{}; // return empty expression
} // convertWhileStmtBit()

slang::SlangExpr slang::SpirGen::convertDoStmt(const DoStmt *doStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string doEntry = "DoEntry" + id;
  std::string doCond = "DoCond" + id;
  std::string doExit = "DoExit" + id;

  stu.pushLabels(doCond, doExit);

  // do body
  addLabelInstr(doEntry);
  const Stmt *body = doStmt->getBody();
  if (body) {
    convertStmt(body);
  }

  // while condition
  addLabelInstr(doCond);
  const Stmt *condition = doStmt->getCond();
  SlangExpr conditionExpr = convertToIfTmp(convertStmt(condition));
  addCondInstr(conditionExpr.expr, doEntry, doExit,
               getLocationString(condition));

  addLabelInstr(doExit);

  stu.popLabel();
  return SlangExpr{}; // return empty expression
} // convertDoStmt()

slang::SlangBitExpr slang::SpirGen::convertDoStmtBit(const DoStmt *doStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string doEntry = "DoEntry" + id;
  std::string doCond = "DoCond" + id;
  std::string doExit = "DoExit" + id;

  auto doEntryBit = createLabelBit(doEntry, getSrcLocBit(doStmt));
  auto doCondBit = createLabelBit(doCond, getSrcLocBit(doStmt));
  auto doExitBit = createLabelBit(doExit, getSrcLocBit(doStmt));

  stu.pushLabelsBit(doEntryBit, doExitBit);

  // do body
  addLabelInstrBit(doEntryBit, getSrcLocBit(doStmt));
  const Stmt *body = doStmt->getBody();
  if (body) {
    convertStmtBit(body);
  }

  // while condition
  addLabelInstrBit(doCondBit, getSrcLocBit(doStmt));
  const Stmt *condition = doStmt->getCond();
  SlangBitExpr conditionExpr = convertToIfTmpBit(convertStmtBit(condition));
  addCondInstrBit(conditionExpr, doEntryBit, doExitBit, getSrcLocBit(doStmt));

  addLabelInstrBit(doExitBit, getSrcLocBit(doStmt));

  stu.popLabelBit();
  return SlangBitExpr{}; // return empty expression
} // convertDoStmtBit()

slang::SlangExpr slang::SpirGen::convertForStmt(const ForStmt *forStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string forCondLabel = id + "ForCond";
  std::string forBodyLabel = id + "ForBody";
  std::string forExitLabel = id + "ForExit";

  stu.pushLabels(forCondLabel, forExitLabel);

  // for init
  const Stmt *init = forStmt->getInit();
  if (init) {
    convertStmt(init);
  }

  // for condition
  const Stmt *condition = forStmt->getCond();

  addLabelInstr(forCondLabel);

  if (condition) {
    SlangExpr conditionExpr = convertToIfTmp(convertStmt(condition));

    addCondInstr(conditionExpr.expr, forBodyLabel, forExitLabel,
                 getLocationString(condition));
  } else {
    addCondInstr("expr.LitE(1)", forBodyLabel, forExitLabel,
                 getLocationString(forStmt));
  }

  // for body
  addLabelInstr(forBodyLabel);

  const Stmt *body = forStmt->getBody();
  if (body) {
    convertStmt(body);
  }

  const Stmt *inc = forStmt->getInc();
  if (inc) {
    convertStmt(inc);
  }

  addGotoInstr(forCondLabel);  // jump to for cond
  addLabelInstr(forExitLabel); // for exit

  stu.popLabel();
  return SlangExpr{}; // return empty expression
} // convertForStmt()

slang::SlangBitExpr slang::SpirGen::convertForStmtBit(const ForStmt *forStmt) {
  std::string id = stu.genNextLabelCountStr();
  std::string forCondLabel = id + "ForCond";
  std::string forBodyLabel = id + "ForBody";
  std::string forExitLabel = id + "ForExit";

  auto forCondBit = createLabelBit(forCondLabel, getSrcLocBit(forStmt));
  auto forBodyBit = createLabelBit(forBodyLabel, getSrcLocBit(forStmt));
  auto forExitBit = createLabelBit(forExitLabel, getSrcLocBit(forStmt));

  stu.pushLabelsBit(forCondBit, forExitBit);

  // for init
  const Stmt *init = forStmt->getInit();
  if (init) {
    convertStmtBit(init);
  }

  // for condition
  const Stmt *condition = forStmt->getCond();

  addLabelInstrBit(forCondBit, getSrcLocBit(forStmt));

  if (condition) {
    SlangBitExpr conditionExpr = convertToIfTmpBit(convertStmtBit(condition));
    addCondInstrBit(conditionExpr, forBodyBit, forExitBit, getSrcLocBit(forStmt));
  } else {
    addCondInstrBit(createLiteralBitExpr_Integer(1, true, getSrcLocBit(forStmt)), forBodyBit, forExitBit, getSrcLocBit(forStmt));
  }

  // for body
  addLabelInstrBit(forBodyBit, getSrcLocBit(forStmt));

  const Stmt *body = forStmt->getBody();
  if (body) {
    convertStmtBit(body);
  }

  const Stmt *inc = forStmt->getInc();
  if (inc) {
    convertStmtBit(inc);
  }

  addGotoInstrBit(forCondBit, getSrcLocBit(forStmt));  // jump to for cond
  addLabelInstrBit(forExitBit, getSrcLocBit(forStmt)); // for exit

  stu.popLabelBit();
  return SlangBitExpr{}; // return empty expression
} // convertForStmt()

slang::SlangExpr slang::SpirGen::convertCastExpr(const Stmt *expr, QualType qt,
                                          std::string locStr) {
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

slang::SlangExpr
slang::SpirGen::convertImplicitCastExpr(const ImplicitCastExpr *iCast) {
  // only one child is expected
  auto it = iCast->child_begin();
  auto ck = iCast->getCastKind();

  switch (ck) {
  case CastKind::CK_IntegralToFloating:
  case CastKind::CK_FloatingToIntegral:
  case CastKind::CK_IntegralCast:
  case CastKind::CK_ArrayToPointerDecay: {
    return convertStmt(*it);
  }

  default:
    return convertStmt(*it);
    // return convertCastExpr(*it, iCast->getType(), getLocationString(iCast));
  }
} // convertImplicitCastExpr()

slang::SlangBitExpr
slang::SpirGen::convertImplicitCastExprBit(const ImplicitCastExpr *iCast) {
  // only one child is expected
  auto it = iCast->child_begin();
  auto ck = iCast->getCastKind();

  switch (ck) {
  case CastKind::CK_IntegralToFloating:
  case CastKind::CK_FloatingToIntegral:
  case CastKind::CK_IntegralCast:
  case CastKind::CK_ArrayToPointerDecay: {
    return convertStmtBit(*it);
  }

  default:
    return convertStmtBit(*it);
    // return convertCastExpr(*it, iCast->getType(), getLocationString(iCast));
  }
} // convertImplicitCastExprBit()

slang::SlangExpr slang::SpirGen::convertCharacterLiteral(const CharacterLiteral *cl) {
  std::stringstream ss;
  ss << "expr.LitE(" << cl->getValue();
  ss << ", " << getLocationString(cl) << ")";

  SlangExpr slangExpr;
  slangExpr.expr = ss.str();
  slangExpr.locStr = getLocationString(cl);
  slangExpr.qualType = cl->getType();

  return slangExpr;
} // convertCharacterLiteral()

slang::SlangExpr slang::SpirGen::convertConstantExpr(const ConstantExpr *constExpr) {
  // a ConstantExpr contains a literal expression
  return convertStmt(constExpr->getSubExpr());
} // convertConstantExpr()

slang::SlangExpr slang::SpirGen::convertIntegerLiteral(const IntegerLiteral *il) {
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
  charSv->clear();
  il->getValue().toString(*charSv, 10, is_signed);
  ss << charSv->data();
  // il->print(ss, is_signed);// << il->getValue().toString(10, is_signed);
  ss << suffix;
  ss << ", " << locStr << ")";
  SLANG_TRACE(ss.str())

  SlangExpr slangExpr;
  slangExpr.expr = ss.str();
  slangExpr.qualType = il->getType();
  slangExpr.locStr = getLocationString(il);

  return slangExpr;
} // convertIntegerLiteral()

slang::SlangBitExpr slang::SpirGen::convertIntegerLiteralBit(const IntegerLiteral *il) {
  bool isFloat = false;

  SLANG_PRINT("convertIntegerLiteralBit: " << il->getValue().getLimitedValue());
  SLANG_DEBUG_GUARD(il->dump(););
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
          isFloat = true;
          break;
        }
      }
      }
    }
  }

  SLANG_PRINT("isFloat: " << isFloat);
  bool is_signed = il->getType()->isSignedIntegerType();
  if (isFloat) {
    return createLiteralBitExpr_Floating(il->getValue().getLimitedValue(), getSrcLocBit(il));
  }
  return createLiteralBitExpr_Integer(il->getValue().getLimitedValue(), is_signed, getSrcLocBit(il));
} // convertIntegerLiteralBit()

slang::SlangExpr slang::SpirGen::convertFloatingLiteral(const FloatingLiteral *fl) {
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

slang::SlangExpr slang::SpirGen::convertStringLiteral(const StringLiteral *sl) {
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

slang::SlangExpr
slang::SpirGen::convertVariable(const VarDecl *varDecl, std::string locStr) {
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

slang::SlangBitExpr
slang::SpirGen::convertVariableBit(const VarDecl *varDecl, SrcLoc srcLoc) {
  SlangBitExpr sbExpr;
  uint64_t varAddr = (uint64_t)varDecl;
  // auto varName = stu.convertVarExpr(varAddr); // keeping for reference
  sbExpr.bitExpr = createBitExpr(createBitEntity(varAddr, srcLoc));
  sbExpr.bitExpr->set_xkind(spir::K_XK::XVAL);
  sbExpr.bitExpr->set_oprnd1eid(varAddr);
  sbExpr.bitExpr->set_loc_line(srcLoc.line);
  sbExpr.bitExpr->set_loc_col(srcLoc.col);
  sbExpr.bitExpr->set_oprnd1_line(srcLoc.line);
  sbExpr.bitExpr->set_oprnd1_col(srcLoc.col);

  return sbExpr;
} // convertVariableBit()

spir::BitEntity slang::SpirGen::convertVarDeclToBitEntity(const VarDecl *varDecl) {
  spir::BitEntity be;
  be.set_eid((uint64_t)varDecl);
  SrcLoc srcLoc = getSrcLocBit(varDecl);
  be.set_line(srcLoc.line);
  be.set_col(srcLoc.col);
  return be;
} // convertVarDeclToBitEntity()

void slang::SpirGen::addBitExprOperand1(spir::BitExpr *expr, spir::BitEntity be) {
  expr->set_oprnd1eid(be.eid());
  expr->set_oprnd1_line(be.line());
  expr->set_oprnd1_col(be.col());
}

void slang::SpirGen::addBitExprOperand2(spir::BitExpr *expr, spir::BitEntity be) {
  expr->set_oprnd2eid(be.eid());
  expr->set_oprnd2_line(be.line());
  expr->set_oprnd2_col(be.col());
}

spir::BitExpr *slang::SpirGen::createBitExpr(spir::BitEntity be) {
  spir::BitExpr *expr = new spir::BitExpr();

  // Assumes a simple expression with no operators.
  expr->set_xkind(spir::K_XK::XVAL);

  // Set the first operand only.
  expr->set_oprnd1eid(be.eid());

  // Use the same src location for operand 1 and the expression.
  expr->set_oprnd1_line(be.line());
  expr->set_oprnd1_col(be.col());
  expr->set_loc_line(be.line());
  expr->set_loc_col(be.col());
  return expr;
} // createBitExpr()

spir::BitExpr *slang::SpirGen::createBitExpr(spir::K_XK op, spir::BitEntity be1, spir::BitEntity be2,
                                       SrcLoc srcLoc) {
  spir::BitExpr *expr = new spir::BitExpr();
  expr->set_xkind(op);

  expr->set_oprnd1eid(be1.eid());
  expr->set_oprnd1_line(be1.line());
  expr->set_oprnd1_col(be1.col());

  expr->set_oprnd2eid(be2.eid());
  expr->set_oprnd2_line(be2.line());
  expr->set_oprnd2_col(be2.col());

  expr->set_loc_line(srcLoc.line);
  expr->set_loc_col(srcLoc.col);
  return expr;
} // createBitExpr()

// Extracts the spir::BitEntity from the spir::BitExpr.
// It assumes the entity is the first operand of the expression.
spir::BitEntity slang::SpirGen::convertBitExprToBitEntity(spir::BitExpr *expr, bool freeExpr) {
  assert(expr != nullptr);

  if (expr->xkind() != spir::K_XK::XVAL) {
    SLANG_ERROR("ERROR: Not a value expression: " << K_XK_Name(expr->xkind()));
    return spir::BitEntity{};
  }

  spir::BitEntity be;
  be.set_eid(expr->oprnd1eid());
  be.set_line(expr->oprnd1_line());
  be.set_col(expr->oprnd1_col());

  if (freeExpr) {
    delete expr;
  }
  return be;
} // convertBitExprToBitEntity()

slang::SlangExpr slang::SpirGen::convertSlangVar(SlangVar &slangVar,
                                          const VarDecl *varDecl) {
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

slang::SlangBitExpr slang::SpirGen::convertSlangVarBit(uint64_t eid,
                                                const VarDecl *varDecl) {
  SlangBitExpr slangBitExpr;

  slangBitExpr.bitExpr = createBitExpr(createBitEntity(eid));

  return slangBitExpr;
} // convertSlangVarBit()

spir::BitEntity slang::SpirGen::createBitEntity(uint64_t eid, SrcLoc srcLoc) {
  spir::BitEntity be;
  be.set_eid(eid);
  be.set_line(srcLoc.line);
  be.set_col(srcLoc.col);
  return be;
} // createBitEntity()

slang::SlangExpr slang::SpirGen::convertEnumConst(const EnumConstantDecl *ecd,
                                           std::string &locStr) {
  SlangExpr slangExpr;

  std::stringstream ss;
  auto value = ecd->getInitVal();
  charSv->clear();
  value.toString(*charSv, 10, value.isSigned());
  ss << "expr.LitE(" << charSv->data();
  ss << ", " << locStr << ")";

  slangExpr.expr = ss.str();
  slangExpr.locStr = locStr;
  slangExpr.qualType = ecd->getType();

  return slangExpr;
} // convertEnumConst()

slang::SlangBitExpr slang::SpirGen::convertEnumConstBit(const EnumConstantDecl *ecd, SrcLoc srcLoc) {
  SlangBitExpr slangBitExpr;

  auto value = ecd->getInitVal();
  slangBitExpr = createLiteralBitExpr_Integer(value.getLimitedValue(),
      value.isSigned(), srcLoc);

  return slangBitExpr;
} // convertEnumConstBit()

slang::SlangExpr slang::SpirGen::convertDeclRefExpr(const DeclRefExpr *dre) {
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

slang::SlangBitExpr slang::SpirGen::convertDeclRefExprBit(const DeclRefExpr *dre) {
  SlangBitExpr sbExpr;

  const ValueDecl *valueDecl = dre->getDecl();
  if (isa<EnumConstantDecl>(valueDecl)) {
    auto ecd = cast<EnumConstantDecl>(valueDecl);
    return convertEnumConstBit(ecd, getSrcLocBit(dre));
  }

  // it may be a VarDecl or FunctionDecl
  handleValueDecl(valueDecl, stu.currFunc->name);

  if (isa<VarDecl>(valueDecl)) {
    auto varDecl = cast<VarDecl>(valueDecl);
    sbExpr = convertVariableBit(varDecl, getSrcLocBit(dre));
    return sbExpr;

  } else if (isa<FunctionDecl>(valueDecl)) {
    const FunctionDecl *funcDecl = cast<FunctionDecl>(valueDecl);
    uint64_t funcAddr = (uint64_t)funcDecl;
    sbExpr.bitExpr = createBitExpr(createBitEntity(funcAddr, getSrcLocBit(dre)));
    sbExpr.bitExpr->set_xkind(spir::K_XK::XVAL);
    sbExpr.bitExpr->set_oprnd1eid(funcAddr);
    sbExpr.bitExpr->set_oprnd1_line(getSrcLocBit(dre).line);
    sbExpr.bitExpr->set_oprnd1_col(getSrcLocBit(dre).col);
    sbExpr.bitExpr->set_loc_line(getSrcLocBit(dre).line);
    sbExpr.bitExpr->set_loc_col(getSrcLocBit(dre).col);
    sbExpr.qualType = funcDecl->getType();
    sbExpr.varId = funcAddr;
    return sbExpr;
  } else {
    SLANG_ERROR("Not_a_VarDecl or FunctionDecl.")
    return sbExpr;
  }
} // convertDeclRefExprBit()

// a || b , a && b
slang::SlangExpr slang::SpirGen::convertLogicalOp(const BinaryOperator *binOp) {
  std::string nextCheck;
  std::string tmpReAssign;
  std::string exitLabel;

  std::string op;
  std::string id = stu.genNextLabelCountStr();
  switch (binOp->getOpcode()) {
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
  default:
    SLANG_ERROR("ERROR:UnknownLogicalOp");
    break;
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
  SlangExpr tmpVar =
      genTmpVariable("L", "types.Int32", getLocationString(binOp));
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

// a || b , a && b
slang::SlangBitExpr slang::SpirGen::convertLogicalOpBit(const BinaryOperator *binOp) {
  std::string nextCheck;
  std::string tmpReAssign;
  std::string exitLabel;

  std::string op;
  std::string id = stu.genNextLabelCountStr();
  switch (binOp->getOpcode()) {
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
  default:
    SLANG_ERROR("ERROR:UnknownLogicalOp");
    break;
  }

  spir::BitEntity nextCheckLabelBit = createLabelBit(nextCheck, getSrcLocBit(binOp));
  spir::BitEntity tmpReAssignLabelBit =
      createLabelBit(tmpReAssign, getSrcLocBit(binOp));
  spir::BitEntity exitLabelBit = createLabelBit(exitLabel, getSrcLocBit(binOp));

  auto it = binOp->child_begin();
  const Stmt *leftOprStmt = *it;
  ++it;
  const Stmt *rightOprStmt = *it;

  auto trueValue = createLiteralBitExpr_Integer(1, false, getSrcLocBit(binOp));
  auto falseValue = createLiteralBitExpr_Integer(0, false, getSrcLocBit(binOp));

  // assign tmp = 1
  auto tmpVar =
      createBitExpr(genTmpBitEntity(spir::K_VK::TINT32, "L", getSrcLocBit(binOp)));
  addAssignBitInstr(tmpVar, trueValue);

  // check first part "a ||" or "a &&"
  SlangBitExpr leftOprExpr = convertToIfTmpBit(convertStmtBit(leftOprStmt));
  if (op == "||") {
    addCondInstrBit(leftOprExpr, exitLabelBit, nextCheckLabelBit,
                    getSrcLocBit(leftOprStmt));
  } else { // && operator
    addCondInstrBit(leftOprExpr, nextCheckLabelBit, tmpReAssignLabelBit,
                    getSrcLocBit(leftOprStmt));
  }

  // check second part || b, && b
  addLabelInstrBit(nextCheckLabelBit, getSrcLocBit(rightOprStmt));
  SlangBitExpr rightOprExpr = convertToIfTmpBit(convertStmtBit(rightOprStmt));
  addCondInstrBit(rightOprExpr, exitLabelBit, tmpReAssignLabelBit,
                  getSrcLocBit(rightOprStmt));

  // assign tmp = 0
  addLabelInstrBit(tmpReAssignLabelBit, getSrcLocBit(rightOprStmt) );
  addAssignBitInstr(tmpVar, falseValue);

  // exit label
  addLabelInstrBit(exitLabelBit, getSrcLocBit(rightOprStmt));

  return tmpVar;
} // convertLogicalOpBit()

slang::SlangExpr slang::SpirGen::convertUnaryIncDecOp(const UnaryOperator *unOp) {
  auto it = unOp->child_begin();
  SlangExpr exprArg = convertStmt(*it);

  std::string op;
  switch (unOp->getOpcode()) {
  case UO_PreInc:
  case UO_PostInc:
    op = "op.BO_ADD";
    break;
  case UO_PostDec:
  case UO_PreDec:
    op = "op.BO_SUB";
    break;
  default:
    break;
  }

  SlangExpr litOne;
  litOne.expr = "expr.LitE(1, " + getLocationString(unOp) + ")";
  litOne.locStr = getLocationString(unOp);

  SlangExpr incDecExpr = createBinaryExpr(
      exprArg, op, litOne, getLocationString(unOp), exprArg.qualType);

  switch (unOp->getOpcode()) {
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
    SLANG_ERROR("ERROR:UnknownIncDecOps"
                << unOp->getOpcodeStr(unOp->getOpcode()));
    break;
  }
  return exprArg;
}

spir::K_VK slang::SpirGen::getIntegerValueKind(uint64_t value, bool isSigned) {
  // Returns the most fitting integer value kind based on value and sign.
  // spir::K_VK is the value kind enum (e.g. TUINT8, TINT16, etc.)
  spir::K_VK kind;
  if (isSigned) {
    if (value <= static_cast<uint64_t>(std::numeric_limits<int8_t>::max())) {
      kind = spir::K_VK::TINT8;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<int16_t>::max())) {
      kind = spir::K_VK::TINT16;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<int32_t>::max())) {
      kind = spir::K_VK::TINT32;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<int64_t>::max())) {
      kind = spir::K_VK::TINT64;
    } else {
      kind =
          spir::K_VK::TINT64; // Assume TINT128 as TINT64 bit signed integer
    }
  } else { // unsigned
    if (value <= static_cast<uint64_t>(std::numeric_limits<uint8_t>::max())) {
      kind = spir::K_VK::TUINT8;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<uint16_t>::max())) {
      kind = spir::K_VK::TUINT16;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<uint32_t>::max())) {
      kind = spir::K_VK::TUINT32;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<uint64_t>::max())) {
      kind = spir::K_VK::TUINT64;
    } else {
      kind = spir::K_VK::TUINT64; // Assume TUINT128 as TUINT64 bit unsigned integer
    }
  }
  return kind;
} // getIntegerValueKind()

/// Returns the most fitting QualType from the value and its signedness.
QualType slang::SpirGen::getIntegerValueQualType(uint64_t value,
                                                 bool isSigned) {
  // Note: This function assumes common primitive integer types are available:
  // Ctx->CharTy, Ctx->ShortTy, Ctx->IntTy, Ctx->LongTy, Ctx->LongLongTy, and
  // their unsigned versions. If you have custom types, adjust as needed.

  // Check signed types first
  if (isSigned) {
    if (value <= static_cast<uint64_t>(std::numeric_limits<int8_t>::max())) {
      return Ctx->CharTy;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<int16_t>::max())) {
      return Ctx->ShortTy;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<int32_t>::max())) {
      return Ctx->IntTy;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<int64_t>::max())) {
      return Ctx->LongLongTy;
    } else {
      // If value does not fit in 64-bit signed, use a custom 128-bit type if
      // available Fallback to largest available type
      if (Ctx->Int128Ty.isNull()) {
        return Ctx->LongLongTy;
      }
      return Ctx->Int128Ty;
    }
  } else { // unsigned types
    if (value <= static_cast<uint64_t>(std::numeric_limits<uint8_t>::max())) {
      return Ctx->UnsignedCharTy;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<uint16_t>::max())) {
      return Ctx->UnsignedShortTy;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<uint32_t>::max())) {
      return Ctx->UnsignedIntTy;
    } else if (value <=
               static_cast<uint64_t>(std::numeric_limits<uint64_t>::max())) {
      return Ctx->UnsignedLongLongTy;
    } else {
      // If value does not fit in 64-bit unsigned, use a custom 128-bit type if
      // available
      if (Ctx->UnsignedInt128Ty.isNull()) {
        return Ctx->UnsignedLongLongTy;
      }
      return Ctx->UnsignedInt128Ty;
    }
  }
} // getIntegerValueQualType()

slang::SlangBitExpr
slang::SpirGen::createLiteralBitExpr_Integer(uint64_t value, bool isSigned,
                                             slang::SrcLoc srcLoc) {
  SlangBitExpr slangExpr;
  uint64_t entityId = stu.nextUniqueId();
  // Create a BitEntityInfo object and set its value and source location
  spir::BitEntityInfo bitEntityInfo = spir::BitEntityInfo();
  bitEntityInfo.set_eid(entityId);
  bitEntityInfo.set_ekind(spir::K_EK::ELIT_NUM); // Numeric literal entity kind
  bitEntityInfo.set_vkind(getIntegerValueKind(value, isSigned));
  bitEntityInfo.set_lowval(value);  
  bitEntityInfo.set_loc_line(srcLoc.line);
  bitEntityInfo.set_loc_col(srcLoc.col);
  stu.bittu.mutable_entityinfo()->insert({entityId, bitEntityInfo});

  // Create BitEntity from BitEntityInfo and entityId
  spir::BitEntity bitEntity;
  bitEntity.set_eid(entityId);
  bitEntity.set_line(srcLoc.line);
  bitEntity.set_col(srcLoc.col);

  // Create BitExpr from the BitEntity with VAL operator type
  spir::BitExpr *bitExpr = new spir::BitExpr();
  bitExpr->set_xkind(spir::K_XK::XVAL);
  addBitExprOperand1(bitExpr,bitEntity);
  bitExpr->set_loc_line(srcLoc.line);
  bitExpr->set_loc_col(srcLoc.col);

  // Initialize the SlangBitExpr and assign the BitExpr
  slangExpr.bitExpr = bitExpr;
  slangExpr.compound = false;
  slangExpr.qualType = getIntegerValueQualType(value, isSigned);

  return slangExpr;
} // createLiteralBitExpr_Integer()

slang::SlangBitExpr
slang::SpirGen::createLiteralBitExpr_Floating(double value, slang::SrcLoc srcLoc) {
  SlangBitExpr slangExpr;
  // Create a BitEntityInfo object and set its value and source location
  spir::BitEntityInfo bitEntityInfo;
  bitEntityInfo.set_ekind(spir::K_EK::ELIT_NUM); // Numeric literal entity kind
  bitEntityInfo.set_vkind(spir::K_VK::TFLOAT64);
  bitEntityInfo.set_lowval(slang::Util::double_to_u64(value));
  bitEntityInfo.set_loc_line(srcLoc.line);
  bitEntityInfo.set_loc_col(srcLoc.col);

  uint64_t entityId = stu.nextUniqueId();
  stu.bittu.mutable_entityinfo()->insert({entityId, bitEntityInfo});

  // Create BitEntity from BitEntityInfo and entityId
  spir::BitEntity bitEntity;
  bitEntity.set_eid(entityId);
  bitEntity.set_line(srcLoc.line);
  bitEntity.set_col(srcLoc.col);

  // Create BitExpr from the BitEntity with VAL operator type
  spir::BitExpr *bitExpr = new spir::BitExpr();
  bitExpr->set_xkind(spir::K_XK::XVAL);
  addBitExprOperand1(bitExpr,bitEntity);
  bitExpr->set_loc_line(srcLoc.line);
  bitExpr->set_loc_col(srcLoc.col);

  // Initialize the SlangBitExpr and assign the BitExpr
  slangExpr.bitExpr = bitExpr;
  slangExpr.compound = false;
  slangExpr.qualType = Ctx->FloatTy;
  slangExpr.varId = entityId;

  return slangExpr;
} // createLiteralBitExpr_Floating()

slang::SlangBitExpr
slang::SpirGen::convertUnaryIncDecOpBit(const UnaryOperator *unOp) {
  auto it = unOp->child_begin();
  SlangBitExpr bitExprArg = convertStmtBit(*it);

  spir::K_XK incDecOp;
  switch (unOp->getOpcode()) {
  case UO_PreInc:
  case UO_PostInc:
    incDecOp = spir::K_XK::XADD;
    break;
  case UO_PostDec:
  case UO_PreDec:
    incDecOp = spir::K_XK::XSUB;
    break;
  default:
    break;
  }

  SlangBitExpr litOne =
      createLiteralBitExpr_Integer(1, false, getSrcLocBit(unOp));

  // Expression to add or subtract constant 1.
  SlangBitExpr incDecExpr = createBinaryBitExpr(
      bitExprArg /*left operand*/, incDecOp, litOne /*right operand*/,
      getSrcLocBit(unOp), bitExprArg.qualType);

  switch (unOp->getOpcode()) {
  case UO_PreInc:
  case UO_PreDec: {
    addAssignBitInstr(bitExprArg, incDecExpr);
    incDecExpr.deleteBitExpr();
    return convertToTmpBitExpr(bitExprArg, true); // FIXME: why force=true?
  }

  case UO_PostInc:
  case UO_PostDec: {
    // Keep the original value in a temporary and return it.
    // In the current expression the temporary gets used.
    // Assign the inc/decremented value in the original variable.
    SlangBitExpr tmpExpr = convertToTmpBitExpr(bitExprArg, true);
    addAssignBitInstr(bitExprArg, incDecExpr);
    incDecExpr.deleteBitExpr();
    return tmpExpr;
  }

  default:
    SLANG_ERROR("ERROR:UnknownIncDecOps"
                << unOp->getOpcodeStr(unOp->getOpcode()));
    break;
  }
  return SlangBitExpr{}; // FIXME
} // convertUnaryIncDecOpBit()

slang::SlangExpr slang::SpirGen::convertUnaryOperator(const UnaryOperator *unOp) {
  switch (unOp->getOpcode()) {
  case UO_PreInc:
  case UO_PostInc:
  case UO_PreDec:
  case UO_PostDec:
    return convertUnaryIncDecOp(unOp);
  default:
    break;
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
  case UO_AddrOf:
    op = "op.UO_ADDROF";
    break;
  case UO_Deref:
    op = "op.UO_DEREF";
    break;
  case UO_Minus:
    op = "op.UO_MINUS";
    break;
  case UO_Plus:
    op = "op.UO_MINUS";
    break;
  case UO_LNot:
    op = "op.UO_LNOT";
    break;
  case UO_Not:
    op = "op.UO_BIT_NOT";
    break;
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

slang::SlangBitExpr
slang::SpirGen::convertUnaryOperatorBit(const UnaryOperator *unOp) {
  switch (unOp->getOpcode()) {
  case UO_PreInc:
  case UO_PostInc:
  case UO_PreDec:
  case UO_PostDec:
    return convertUnaryIncDecOpBit(unOp);
  default:
    break;
  }

  // This handles special case too: e.g. &arr[7][5], ...
  auto it = unOp->child_begin();
  SlangBitExpr sbExpr = convertToTmpBitExpr(convertStmtBit(*it), false, true);

  spir::K_XK opKind;
  switch (unOp->getOpcode()) {
  default:
    SLANG_DEBUG("convertUnaryOp: " << unOp->getOpcodeStr(unOp->getOpcode()))
    break;
  case UO_AddrOf:
    opKind = spir::K_XK::XADDROF;
    break;
  case UO_Deref:
    opKind = spir::K_XK::XDEREF;
    break;
  case UO_Minus:
    opKind = spir::K_XK::XNEGATE;
    break;
  case UO_Plus:
    opKind = spir::K_XK::XVAL;
    break; // silently remove the + sign
  case UO_LNot:
    opKind = spir::K_XK::XNOT;
    break;
  case UO_Not:
    opKind = spir::K_XK::XBIT_NOT;
    break;
  case UO_Extension:
    // doesn't handle __extension__ expressions -- return a 0 constant instead.
    return createLiteralBitExpr_Integer(0, false, getSrcLocBit(unOp));
  }

  return createUnaryBitExpr(opKind, sbExpr, getSrcLocBit(unOp),
                            getImplicitType(unOp, unOp->getType()));
} // convertUnaryOperatorBit()

slang::SlangExpr slang::SpirGen::convertUnaryExprOrTypeTraitExpr(
    const UnaryExprOrTypeTraitExpr *stmt) {
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
      TypeInfo typeInfo = Ctx->getTypeInfo(stmt->getArgumentType());
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

slang::SlangExpr slang::SpirGen::convertBinaryOperator(const BinaryOperator *binOp) {
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

  case BO_Add:
    op = "op.BO_ADD";
    break;
  case BO_Sub:
    op = "op.BO_SUB";
    break;
  case BO_Mul:
    op = "op.BO_MUL";
    break;
  case BO_Div:
    op = "op.BO_DIV";
    break;
  case BO_Rem:
    op = "op.BO_MOD";
    break;

  case BO_LT:
    op = "op.BO_LT";
    break;
  case BO_LE:
    op = "op.BO_LE";
    break;
  case BO_EQ:
    op = "op.BO_EQ";
    break;
  case BO_NE:
    op = "op.BO_NE";
    break;
  case BO_GE:
    op = "op.BO_GE";
    break;
  case BO_GT:
    op = "op.BO_GT";
    break;

  case BO_Or:
    op = "op.BO_BIT_OR";
    break;
  case BO_And:
    op = "op.BO_BIT_AND";
    break;
  case BO_Xor:
    op = "op.BO_BIT_XOR";
    break;

  case BO_Shl:
    op = "op.BO_LSHIFT";
    break;
  case BO_Shr:
    op = "op.BO_RSHIFT";
    break;

  case BO_Comma:
    return convertBinaryCommaOp(binOp);

  default:
    op = "ERROR:binOp";
    break;
  }

  auto it = binOp->child_begin();
  const Stmt *leftOprStmt = *it;
  ++it;
  const Stmt *rightOprStmt = *it;

  SlangExpr leftOprExpr = convertStmt(leftOprStmt);
  SlangExpr rightOprExpr = convertStmt(rightOprStmt);

  slangExpr =
      createBinaryExpr(leftOprExpr, op, rightOprExpr, getLocationString(binOp),
                       getImplicitType(binOp, binOp->getType()));

  return slangExpr;
} // convertBinaryOperator()

slang::SlangBitExpr
slang::SpirGen::convertBinaryOperatorBit(const BinaryOperator *binOp) {
  if (binOp->isCompoundAssignmentOp()) {
    return convertCompoundAssignmentOpBit(binOp);
  } else if (binOp->isAssignmentOp()) {
    return convertAssignmentOpBit(binOp);
  } else if (binOp->isLogicalOp()) {
    return convertLogicalOpBit(binOp);
  }

  spir::K_XK op;
  bool flipOperands = false;
  switch (binOp->getOpcode()) {
    // NOTE : && and || are handled in convertConditionalOp()

  case BO_Add:
    op = spir::K_XK::XADD;
    break;
  case BO_Sub:
    op = spir::K_XK::XSUB;
    break;
  case BO_Mul:
    op = spir::K_XK::XMUL;
    break;
  case BO_Div:
    op = spir::K_XK::XDIV;
    break;
  case BO_Rem:
    op = spir::K_XK::XMOD;
    break;

  case BO_LT:
    op = spir::K_XK::XLT;
    break;
  case BO_LE:
    op = spir::K_XK::XGE;
    flipOperands = true;
    break;
  case BO_EQ:
    op = spir::K_XK::XEQ;
    break;
  case BO_NE:
    op = spir::K_XK::XNE;
    break;
  case BO_GE:
    op = spir::K_XK::XGE;
    break;
  case BO_GT:
    op = spir::K_XK::XLT;
    flipOperands = true;
    break;

  case BO_Or:
    op = spir::K_XK::XOR;
    break;
  case BO_And:
    op = spir::K_XK::XAND;
    break;
  case BO_Xor:
    op = spir::K_XK::XXOR;
    break;

  case BO_Shl:
    op = spir::K_XK::XSHL;
    break;
  case BO_Shr:
    op = spir::K_XK::XSHR;
    break;

  case BO_Comma:
    return convertBinaryCommaOpBit(binOp);

  default:
    op = spir::K_XK::XNIL;
    break;
  }

  auto it = binOp->child_begin();
  const Stmt *leftOprStmt = *it;
  ++it;
  const Stmt *rightOprStmt = *it;

  SlangBitExpr leftOprExpr = convertStmtBit(leftOprStmt);
  SlangBitExpr rightOprExpr = convertStmtBit(rightOprStmt);

  SlangBitExpr sbExpr;
  if (flipOperands) {
    // Used to replace GT with LT and LE with GE by flipping the operands.
    sbExpr = createBinaryBitExpr(rightOprExpr, op, leftOprExpr,
                                 getSrcLocBit(binOp),
                                 getImplicitType(binOp, binOp->getType()));
  } else {
    sbExpr = createBinaryBitExpr(leftOprExpr, op, rightOprExpr,
                                 getSrcLocBit(binOp),
                                 getImplicitType(binOp, binOp->getType()));
  }

  leftOprExpr.deleteBitExpr();
  rightOprExpr.deleteBitExpr();
  return sbExpr;
} // convertBinaryOperatorBit()

// stores the given expression into a tmp variable
slang::SlangExpr slang::SpirGen::convertToTmp(SlangExpr slangExpr, bool force) {
  if (slangExpr.compound || force == true) {
    SlangExpr tmpExpr;
    if (slangExpr.qualType.isNull() ||
        slangExpr.qualType.getTypePtr()->isVoidType()) {
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

// Stores the given expression into a tmp variable if it is compound,
// or the force flag is true.
// To assign constant literals to a temporary, use force = true.
slang::SlangBitExpr slang::SpirGen::convertToTmpBitExpr(SlangBitExpr expr, bool force, bool gc) {
  // STEP 1: Return the expr unchanged if it is a simple value (unless forced
  // otherwise)
  if (force == false) {
    if (!expr.compound || expr.bitExpr->xkind() == spir::K_XK::XVAL) {
      return expr;
    }
  }

  // STEP 2: If here, it is a compound expression or a forced temporary
  // assignment, hence create a new temporary, assign the expression to it and
  // return the temporary.
  spir::BitEntity bEntity;
  // Always use a default signed 32-bit int type for tmpVarType.
  QualType tmpVarType = Ctx->getIntTypeForBitwidth(32, /*Signed=*/true);
  if (expr.qualType.isNull() || expr.qualType.getTypePtr()->isVoidType()) {
      bEntity = genTmpBitEntity(spir::K_VK::TINT32, "t", expr.srcLoc());
  } else {
    if (expr.qualType.getTypePtr()->isArrayType()) {
      // for array type, generate a tmp variable which is a pointer
      // to its element types.
      const Type *type = expr.qualType.getTypePtr();
      const ArrayType *arrayType = type->getAsArrayTypeUnsafe();
      QualType elementType = arrayType->getElementType();
      tmpVarType = Ctx->getPointerType(elementType);
      bEntity = genTmpBitEntity(spir::K_VK::TNIL, "t", expr.srcLoc(), tmpVarType);
    } else if (expr.qualType.getTypePtr()->isFunctionType()) {
      // create a tmp variable which is a pointer to the function type
      tmpVarType = Ctx->getPointerType(expr.qualType);
      bEntity = genTmpBitEntity(spir::K_VK::TNIL, "t", expr.srcLoc(), tmpVarType);
    } else {
      tmpVarType = expr.qualType;
      // Use signed 32-bit as tmpVarType (set above), but pass expr.qualType for
      // semantic fidelity.
      bEntity = genTmpBitEntity(spir::K_VK::TNIL, "t", expr.srcLoc(), tmpVarType);
    }
  }

  spir::BitExpr *bExpr = createBitExpr(bEntity);
  SlangBitExpr sbExpr = createSlangExprFromBitExpr(bExpr, tmpVarType, true);
  addAssignBitInstr(sbExpr, expr);
  if (gc == true) {
    expr.deleteBitExpr();
  }
  return sbExpr;
} // convertToTmpBitExpr()

slang::SlangBitExpr slang::SpirGen::createSlangExprFromBitExpr(spir::BitExpr *bitExpr, QualType type, bool isTmp) {
  SlangBitExpr slangBitExpr;

  slangBitExpr.bitExpr = bitExpr;
  slangBitExpr.qualType = type;
  slangBitExpr.nonTmpVar = !isTmp;
  slangBitExpr.compound = isBitExprCompound(bitExpr);

  return slangBitExpr;
}

// stores the given expression into a tmp variable
slang::SlangBitExpr
slang::SpirGen::convertToTmp2BitExpr(SlangBitExpr slangExpr, bool force, bool gc) {
  if (slangExpr.compound || force == true) {
    spir::BitEntity tmpEntity;
    if (slangExpr.qualType.isNull() ||
        slangExpr.qualType.getTypePtr()->isVoidType()) {
      tmpEntity = genTmpBitEntity(spir::K_VK::TINT32, "t", slangExpr.srcLoc());

    } else {
      if (slangExpr.qualType.getTypePtr()->isArrayType()) {
        // for array type, generate a tmp variable which is a pointer
        // to its element types.
        const Type *type = slangExpr.qualType.getTypePtr();
        const ArrayType *arrayType = type->getAsArrayTypeUnsafe();
        QualType elementType = arrayType->getElementType();
        QualType tmpVarType = Ctx->getPointerType(elementType);
        tmpEntity = genTmpBitEntity(spir::K_VK::TNIL, "t", slangExpr.srcLoc(), tmpVarType);

      } else if (slangExpr.qualType.getTypePtr()->isFunctionType()) {
        // create a tmp variable which is a pointer to the function type
        QualType tmpVarType = Ctx->getPointerType(slangExpr.qualType);
        tmpEntity = genTmpBitEntity(spir::K_VK::TNIL, "t", slangExpr.srcLoc(), tmpVarType);

      } else if (slangExpr.qualType.getTypePtr()->isRecordType()) {
        QualType recordPtr = Ctx->getPointerType(slangExpr.qualType);
        tmpEntity = genTmpBitEntity(spir::K_VK::TNIL, "t", slangExpr.srcLoc(), recordPtr);
        slangExpr = createUnaryBitExpr(spir::K_XK::XADDROF, slangExpr,
            slangExpr.srcLoc(), recordPtr);

      } else {
        tmpEntity = genTmpBitEntity(spir::K_VK::TNIL, "t", slangExpr.srcLoc(), slangExpr.qualType);
      }
    }

    SlangBitExpr tmpExpr = createBitExpr(tmpEntity);
    addAssignBitInstr(tmpExpr, slangExpr);
    return tmpExpr;
  } else {
    return slangExpr;
  }
} // convertToTmp2BitExpr()

// stores the given expression into a tmp variable
slang::SlangExpr slang::SpirGen::convertToTmp2(SlangExpr slangExpr, bool force) {

  if (slangExpr.compound || force == true) {
    bool takeAddress = false;
    SlangExpr tmpExpr;
    if (slangExpr.qualType.isNull() ||
        slangExpr.qualType.getTypePtr()->isVoidType()) {
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
      } else if (slangExpr.qualType.getTypePtr()->isRecordType()) {
        takeAddress = true;
        tmpExpr = genTmpVariable("t", Ctx->getPointerType(slangExpr.qualType),
                                 slangExpr.locStr);
      } else {
        tmpExpr = genTmpVariable("t", slangExpr.qualType, slangExpr.locStr);
      }
    }
    std::stringstream ss;

    if (takeAddress) {
      ss << "instr.AssignI(" << tmpExpr.expr << ", ";
      ss << "expr.AddrOfE(" << slangExpr.expr << ", " << slangExpr.locStr
         << ")";
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
slang::SlangExpr slang::SpirGen::convertToIfTmp(SlangExpr slangExpr, bool force) {
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

// special tmp variable for if "t.1if", "t.2if" etc...
slang::SlangBitExpr slang::SpirGen::convertToIfTmpBit(SlangBitExpr expr, bool force, bool gc) {
  if (expr.compound || force == true) {
    spir::BitEntity tmp =
        genTmpBitEntity(spir::K_VK::TINT32, "if", expr.srcLoc(), expr.qualType);
    SlangBitExpr tmpExpr = SlangBitExpr(createBitExpr(tmp));
    tmpExpr.nonTmpVar = false;
    addAssignBitInstr(tmpExpr, expr);
    if (gc) {
      expr.deleteBitExpr();
    }
    SLANG_PRINT("tmpExpr: \n" << tmpExpr.toString());
    return tmpExpr;
  } else {
    return expr;
  }
} // convertToIfTmpBit()

slang::SlangExpr
slang::SpirGen::convertCompoundAssignmentOp(const BinaryOperator *binOp) {
  auto it = binOp->child_begin();
  const Stmt *lhs = *it;
  const Stmt *rhs = *(++it);

  SlangExpr rhsExpr = convertStmt(rhs);
  SlangExpr lhsExpr = convertStmt(lhs);

  if (lhsExpr.compound && rhsExpr.compound) {
    rhsExpr = convertToTmp(rhsExpr);
  }

  std::string op;
  switch (binOp->getOpcode()) {
  case BO_ShlAssign:
    op = "op.BO_LSHIFT";
    break;
  case BO_ShrAssign:
    op = "op.BO_RSHIFT";
    break;

  case BO_OrAssign:
    op = "op.BO_BIT_OR";
    break;
  case BO_AndAssign:
    op = "op.BO_BIT_AND";
    break;
  case BO_XorAssign:
    op = "op.BO_BIT_XOR";
    break;

  case BO_AddAssign:
    op = "op.BO_ADD";
    break;
  case BO_SubAssign:
    op = "op.BO_SUB";
    break;
  case BO_MulAssign:
    op = "op.BO_MUL";
    break;
  case BO_DivAssign:
    op = "op.BO_DIV";
    break;
  case BO_RemAssign:
    op = "op.BO_MOD";
    break;

  default:
    op = "ERROR:UnknowncompoundAssignOp";
    break;
  }

  SlangExpr newRhsExpr;
  if (lhsExpr.compound) {
    newRhsExpr = convertToTmp(createBinaryExpr(
        lhsExpr, op, rhsExpr, getLocationString(binOp), lhsExpr.qualType));
  } else {
    newRhsExpr = createBinaryExpr(lhsExpr, op, rhsExpr,
                                  getLocationString(binOp), lhsExpr.qualType);
  }

  addAssignInstr(lhsExpr, newRhsExpr, getLocationString(binOp));
  return lhsExpr;
} // convertCompoundAssignmentOp()

slang::SlangBitExpr
slang::SpirGen::convertCompoundAssignmentOpBit(const BinaryOperator *binOp) {
  auto it = binOp->child_begin();
  const Stmt *lhs = *it;
  const Stmt *rhs = *(++it);

  SlangBitExpr rhsExpr = convertStmtBit(rhs);
  SlangBitExpr lhsExpr = convertStmtBit(lhs);

  if (lhsExpr.compound && rhsExpr.compound) {
    rhsExpr = convertToTmpBitExpr(rhsExpr, false, true);
  }

  spir::K_XK op;
  switch (binOp->getOpcode()) {
  case BO_ShlAssign:
    op = spir::K_XK::XSHL;
    break;
  case BO_ShrAssign:
    op = spir::K_XK::XSHR;
    break;

  case BO_OrAssign:
    op = spir::K_XK::XOR;
    break;
  case BO_AndAssign:
    op = spir::K_XK::XAND;
    break;
  case BO_XorAssign:
    op = spir::K_XK::XXOR;
    break;

  case BO_AddAssign:
    op = spir::K_XK::XADD;
    break;
  case BO_SubAssign:
    op = spir::K_XK::XSUB;
    break;
  case BO_MulAssign:
    op = spir::K_XK::XMUL;
    break;
  case BO_DivAssign:
    op = spir::K_XK::XDIV;
    break;
  case BO_RemAssign:
    op = spir::K_XK::XMOD;
    break;

  default:
    op = spir::K_XK::XNIL;
    break;
  }

  SlangBitExpr newRhsExpr;
  newRhsExpr = createBinaryBitExpr(lhsExpr, op, rhsExpr,
                                   getSrcLocBit(binOp), lhsExpr.qualType);
  if (lhsExpr.compound) {
    newRhsExpr = convertToTmpBitExpr(newRhsExpr, false, true);
  }

  addAssignBitInstr(lhsExpr, newRhsExpr);
  newRhsExpr.deleteBitExpr();
  return lhsExpr;
} // convertCompoundAssignmentOp()

slang::SlangExpr slang::SpirGen::convertAssignmentOp(const BinaryOperator *binOp) {
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

slang::SlangBitExpr
slang::SpirGen::convertAssignmentOpBit(const BinaryOperator *binOp) {
  SlangBitExpr lhsExpr, rhsExpr;

  auto it = binOp->child_begin();
  const Stmt *lhs = *it;
  const Stmt *rhs = *(++it);

  rhsExpr = convertStmtBit(rhs);
  lhsExpr = convertStmtBit(lhs);

  if (lhsExpr.compound && rhsExpr.compound) {
    rhsExpr = convertToTmpBitExpr(rhsExpr, false, true);
  }

  addAssignBitInstr(lhsExpr, rhsExpr);
  return lhsExpr;
} // convertAssignmentOp()

slang::SlangExpr
slang::SpirGen::convertCompoundStmt(const CompoundStmt *compoundStmt) {
  SlangExpr slangExpr;

  for (auto it = compoundStmt->body_begin(); it != compoundStmt->body_end();
       ++it) {
    // don't care about the return value
    convertStmt(*it);
  }

  return slangExpr;
} // convertCompoundStmt()

slang::SlangBitExpr
slang::SpirGen::convertCompoundStmtBit(const CompoundStmt *compoundStmt) {
  SlangBitExpr slangExpr;

  for (auto it = compoundStmt->body_begin(); it != compoundStmt->body_end();
       ++it) {
    // don't care about the return value
    convertStmtBit(*it);
  }

  return slangExpr;
} // convertCompoundStmtBit()

slang::SlangExpr slang::SpirGen::convertParenExpr(const ParenExpr *parenExpr) {
  auto it = parenExpr->child_begin(); // should have only one child
  return convertStmt(*it);
} // convertParenExpr()

slang::SlangBitExpr slang::SpirGen::convertParenExprBit(const ParenExpr *parenExpr) {
  auto it = parenExpr->child_begin(); // should have only one child
  return convertStmtBit(*it);
} // convertParenExprBit()

slang::SlangExpr slang::SpirGen::convertLabel(const LabelStmt *labelStmt) {
  SlangExpr slangExpr;
  std::stringstream ss;

  std::string locStr = getLocationString(labelStmt);

  auto firstChild = *labelStmt->child_begin();
  if (isa<CaseStmt>(firstChild) && stu.switchCfls) {
    stu.switchCfls->gotoLabel = labelStmt->getName();
    stu.switchCfls->gotoLabelLocStr = locStr;
    llvm::errs() << "ERROR:LABEL_BEFORE_CASE(CheckTheCFG): "
                 << stu.switchCfls->gotoLabel << "\n";
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

slang::SlangBitExpr slang::SpirGen::convertLabelBit(const LabelStmt *labelStmt) {
  SlangBitExpr slangExpr;

  auto firstChild = *labelStmt->child_begin();
  if (isa<CaseStmt>(firstChild) && stu.switchCfls) {
    stu.switchCfls->gotoLabel = labelStmt->getName();
    llvm::errs() << "ERROR:LABEL_BEFORE_CASE(CheckTheCFG): "
                 << stu.switchCfls->gotoLabel << "\n";
  } else {
    auto labelBit = createLabelBit(labelStmt->getName(), getSrcLocBit(labelStmt));
    slangExpr.bitExpr = createBitExpr(labelBit);
    slangExpr.compound = false;
    slangExpr.varId = labelBit.eid();
    slangExpr.setSrcLoc(getSrcLocBit(labelStmt));

    addLabelInstrBit(labelBit, getSrcLocBit(labelStmt));
  }

  for (auto it = labelStmt->child_begin(); it != labelStmt->child_end(); ++it) {
    convertStmtBit(*it);
  }

  return slangExpr;
} // convertLabelBit()

// BOUND START: type_conversion_routines

// converts clang type to span ir types
std::string slang::SpirGen::convertClangType(QualType qt) {
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

// convertClangTypeBit converts clang type to span ir proto types.
// It uses an existing or a new spir::BitDataType and returns its id (pointer address
// of the qualtype). It returns a slang::MayValue with errorCode 0 if successful.
slang::MayValue slang::SpirGen::convertClangTypeBit(QualType qt) {
  spir::BitDataType dt;
  slang::MayValue result;

  if (qt.isNull()) {
    if (stu.bittu.datatypes().find(uint64_t(K_00_INT32_TYPE_EID)) !=
        stu.bittu.datatypes().end()) {
      return slang::MayValue(OK /*errorCode*/, 0 /*value*/);
    } else {
      // By default, assume the type is int32
      dt.set_vkind(spir::K_VK::TINT32);
      dt.set_typeid_(K_00_INT32_TYPE_EID);
      stu.bittu.mutable_datatypes()->emplace(K_00_INT32_TYPE_EID, dt);
      return slang::MayValue(OK /*errorCode*/, 0 /*value*/);
    }

    return 0;
  }

  qt = getCleanedQualType(qt);
  const Type *typePtr = qt.getTypePtr();
  const uint64_t typeKey = (uint64_t)typePtr;

  // Return the id (pointer address of the qualtype) if it exists.
  if (stu.bittu.datatypes().find(typeKey) != stu.bittu.datatypes().end()) {
    return slang::MayValue(OK /*errorCode*/, typeKey);
  }

  if (typePtr->isBuiltinType()) {
    return convertClangBuiltinTypeBit(qt, typeKey);

  } else if (typePtr->isEnumeralType()) {
    dt.set_vkind(spir::K_VK::TINT32); // Default to int32
    dt.set_typeid_(typeKey);
    stu.bittu.mutable_datatypes()->emplace(typeKey, dt);
    return slang::MayValue(OK, typeKey);

  } else if (typePtr->isFunctionPointerType()) {
    // should be before ->isPointerType() check below
    return convertFunctionPointerTypeBit(qt, typeKey);

  } else if (typePtr->isPointerType()) {
    QualType pqt = typePtr->getPointeeType();
    auto result = convertClangTypeBit(pqt);
    if (result.errorCode) {
      return result;
    }
    dt.set_vkind(getPtrKindBit(stu.bittu.datatypes().at(result.value).vkind()));
    dt.set_subtypeeid(result.value);
    dt.set_typeid_(typeKey);
    stu.bittu.mutable_datatypes()->emplace(typeKey, dt);
    return slang::MayValue(OK, typeKey);

  } else if (typePtr->isRecordType()) {
    const RecordDecl *rdecl;
    if (typePtr->isStructureType()) {
      rdecl = typePtr->getAsStructureType()->getDecl();
    } else if (typePtr->isUnionType()) {
      rdecl = typePtr->getAsUnionType()->getDecl();
    } else {
      return slang::MayValue(ERR(120));
    }
    return convertClangRecordTypeBit(rdecl, typeKey);

  } else if (typePtr->isArrayType()) {
    return convertClangArrayTypeBit(qt, typeKey);

  } else if (typePtr->isFunctionProtoType()) {
    return convertFunctionPrototypeBit(qt, typeKey);

  } else {
    return slang::MayValue(ERR(121));
  }

} // convertClangTypeBit()

// Returns the pointer kind for the given pointee kind
spir::K_VK slang::SpirGen::getPtrKindBit(spir::K_VK pointeeKind) {
  switch (pointeeKind) {
  case spir::K_VK::TINT8:
    return spir::K_VK::TPTR_TO_INT;
  case spir::K_VK::TINT16:
    return spir::K_VK::TPTR_TO_INT;
  case spir::K_VK::TINT32:
    return spir::K_VK::TPTR_TO_INT;
  case spir::K_VK::TINT64:
    return spir::K_VK::TPTR_TO_INT;
  case spir::K_VK::TFLOAT16:
    return spir::K_VK::TPTR_TO_FLOAT;
  case spir::K_VK::TFLOAT32:
    return spir::K_VK::TPTR_TO_FLOAT;
  case spir::K_VK::TFLOAT64:
    return spir::K_VK::TPTR_TO_FLOAT;
  case spir::K_VK::TVOID:
    return spir::K_VK::TPTR_TO_VOID;
  case spir::K_VK::TPTR_TO_PTR:
    return spir::K_VK::TPTR_TO_PTR;
  case spir::K_VK::TUNION:
    return spir::K_VK::TPTR_TO_RECORD;
  case spir::K_VK::TSTRUCT:
    return spir::K_VK::TPTR_TO_RECORD;
  case spir::K_VK::TARR_FIXED:
    return spir::K_VK::TPTR_TO_ARR;
  case spir::K_VK::TARR_VARIABLE:
    return spir::K_VK::TPTR_TO_ARR;
  case spir::K_VK::TARR_PARTIAL:
    return spir::K_VK::TPTR_TO_ARR;
  default:
    return spir::K_VK::TPTR_TO_VOID;
  }
} // getPtrKindBit()

std::string slang::SpirGen::convertClangBuiltinType(QualType qt) {
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
    ss << "types.Float64"; // FIXME: all are considered 64 bit (okay for
                           // analysis purposes)
  } else if (type->isVoidType()) {
    ss << "types.Void";
  } else {
    ss << "ERROR:UnknownBuiltinType.";
  }

  return ss.str();
} // convertClangBuiltinType()

// Returns 0 if successful, non-zero if error
slang::MayValue slang::SpirGen::convertClangBuiltinTypeBit(QualType qt,
                                                    const uint64_t typeKey) {
  spir::BitDataType dt;
  dt.set_typeid_(typeKey);

  const Type *typePtr = qt.getTypePtr();

  if (typePtr->isSignedIntegerType()) {
    if (typePtr->isCharType()) {
      dt.set_vkind(spir::K_VK::TINT8);
    } else if (typePtr->isChar16Type()) {
      dt.set_vkind(spir::K_VK::TINT16);
    } else if (typePtr->isIntegerType()) {
      TypeInfo typeInfo = Ctx->getTypeInfo(qt);
      size_t size = typeInfo.Width;
      if (size == 32) {
        dt.set_vkind(spir::K_VK::TINT32);
      } else if (size == 64) {
        dt.set_vkind(spir::K_VK::TINT64);
      } else {
        return slang::MayValue(ERR(100));
      }
    } else {
      return slang::MayValue(ERR(101));
    }

  } else if (typePtr->isUnsignedIntegerType()) {
    if (typePtr->isCharType()) {
      dt.set_vkind(spir::K_VK::TUINT8);
    } else if (typePtr->isChar16Type()) {
      dt.set_vkind(spir::K_VK::TUINT16);
    } else if (typePtr->isIntegerType()) {
      TypeInfo typeInfo = Ctx->getTypeInfo(qt);
      size_t size = typeInfo.Width;
      if (size == 32) {
        dt.set_vkind(spir::K_VK::TUINT32);
      } else if (size == 64) {
        dt.set_vkind(spir::K_VK::TUINT64);
      } else {
        return slang::MayValue(ERR(102));
      }
    } else {
      return slang::MayValue(ERR(103));
    }

  } else if (typePtr->isFloatingType()) {
    dt.set_vkind(spir::K_VK::TFLOAT64);
  } else if (typePtr->isVoidType()) {
    dt.set_vkind(spir::K_VK::TVOID);
  } else {
    return slang::MayValue(ERR(104));
  }

  stu.bittu.mutable_datatypes()->emplace(typeKey, dt);
  return slang::MayValue(OK, typeKey);
} // convertClangBuiltinTypeBit()

std::string
slang::SpirGen::convertClangRecordType(const RecordDecl *recordDecl,
                                       SlangRecord *&returnSlangRecord) {
  // a hack1 for anonymous decls (it works!) see test 000193.c and its AST!!
  static const RecordDecl *lastAnonymousRecordDecl = nullptr;
  if (recordDecl && recordDecl->getDefinition()) {
    recordDecl = recordDecl->getDefinition();
  }

  if (recordDecl == nullptr) {
    // default to the last anonymous record decl
    return convertClangRecordType(lastAnonymousRecordDecl, returnSlangRecord);
  }

  if (stu.isRecordPresent((uint64_t)recordDecl)) {
    returnSlangRecord =
        &stu.getRecord((uint64_t)recordDecl); // return pointer back
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

  stu.addRecord((uint64_t)recordDecl, slangRecord); // IMPORTANT
  SlangRecord &newSlangRecord =
      stu.getRecord((uint64_t)recordDecl); // IMPORTANT
  returnSlangRecord = &newSlangRecord;     // IMPORTANT

  SlangRecordField slangRecordField;

  SlangRecord *getBackSlangRecord;
  for (auto it = recordDecl->decls_begin(); it != recordDecl->decls_end();
       ++it) {
    if (isa<RecordDecl>(*it)) {
      convertClangRecordType(cast<RecordDecl>(*it), getBackSlangRecord);
    } else if (isa<FieldDecl>(*it)) {
      const FieldDecl *fieldDecl = cast<FieldDecl>(*it);

      slangRecordField.clear();

      if (fieldDecl->getNameAsString() == "") {
        slangRecordField.name =
            newSlangRecord.getNextAnonymousFieldIdStr() + "a";
        slangRecordField.anonymous = true;
      } else {
        slangRecordField.name = fieldDecl->getNameAsString();
        slangRecordField.anonymous = false;
      }

      slangRecordField.type = fieldDecl->getType();
      if (slangRecordField.anonymous) {
        auto slangVar = SlangVar((uint64_t)fieldDecl, slangRecordField.name);
        stu.addVar((uint64_t)fieldDecl, slangVar);
        slangRecordField.typeStr =
            convertClangRecordType(nullptr, slangRecordField.slangRecord);

      } else if (fieldDecl->getType()->isRecordType()) {
        auto type = fieldDecl->getType();
        if (type->isStructureType()) {
          slangRecordField.typeStr =
              convertClangRecordType(type->getAsStructureType()->getDecl(),
                                     slangRecordField.slangRecord);
        } else if (type->isUnionType()) {
          slangRecordField.typeStr = convertClangRecordType(
              type->getAsUnionType()->getDecl(), slangRecordField.slangRecord);
        }
      } else {
        slangRecordField.typeStr = convertClangType(slangRecordField.type);
      }

      newSlangRecord.members.push_back(slangRecordField);
    }
  }

  // store for later use (part-of-hack1))
  lastAnonymousRecordDecl = recordDecl;

  // no need to add newSlangRecord, its a reference to its entry in the
  // stu.recordMap
  return newSlangRecord.toShortString();
} // convertClangRecordType()

slang::MayValue slang::SpirGen::convertClangRecordTypeBit(const RecordDecl *recordDecl,
                                                   const uint64_t typeKey) {
  spir::BitDataType dt;
  dt.set_typeid_(typeKey);

  // a hack1 for anonymous decls (it works!) see test 000193.c and its AST!!
  static const RecordDecl *lastAnonymousRecordDecl = nullptr;

  if (recordDecl == nullptr) {
    assert(lastAnonymousRecordDecl != nullptr);
    // default to the last anonymous record decl
    return convertClangRecordTypeBit(
        lastAnonymousRecordDecl, (uint64_t)lastAnonymousRecordDecl /*typeKey*/);
  }

  if (recordDecl->getDefinition()) {
    recordDecl = recordDecl->getDefinition();
  }

  if (stu.hasTypeKey(typeKey)) {
    // Get the existing record id (it avoids infinite recursion for self
    // referencing records)
    return slang::MayValue(OK, typeKey);
  }

  std::string namePrefix;
  SlangRecord slangRecord;

  // Set the kind of the record and choose the right prefix for the name
  if (recordDecl->isStruct()) {
    namePrefix = "s:";
    dt.set_vkind(spir::K_VK::TSTRUCT);
  } else if (recordDecl->isUnion()) {
    namePrefix = "u:";
    dt.set_vkind(spir::K_VK::TUNION);
  }

  // Set the name of the record, its anonymous flag and source location
  if (recordDecl->getNameAsString() == "") {
    dt.set_anonymous(true);
    dt.set_typename_(namePrefix + stu.getNextRecordIdStr());
  } else {
    dt.set_anonymous(false);
    dt.set_typename_(namePrefix + recordDecl->getNameAsString());
  }
  SrcLoc srcLoc = getSrcLocBit(recordDecl);
  dt.set_loc_line(srcLoc.line);
  dt.set_loc_col(srcLoc.col);

  spir::BitEntityInfo bitEntityInfo;
  bitEntityInfo.set_eid(typeKey);
  bitEntityInfo.set_ekind(spir::K_EK::EDATA_TYPE);
  bitEntityInfo.set_vkind(dt.vkind());
  bitEntityInfo.set_datatypeeid(typeKey); // same as eid for record types
  bitEntityInfo.set_strval(dt.typename_());
  bitEntityInfo.set_anonymous(dt.anonymous());
  bitEntityInfo.set_loc_line(srcLoc.line);
  bitEntityInfo.set_loc_col(srcLoc.col);
  stu.bittu.mutable_entityinfo()->emplace(typeKey, bitEntityInfo);

  // It is nessary to place the incomplete record type in the BitTU.datatypes
  // map, as the record can be recursively referenced by its own fields. This
  // avoids infinite recursion for self referencing records. The record type is
  // placed again when all its fields are populated.
  stu.bittu.mutable_datatypes()->emplace(typeKey, dt);

  // Iterate over each field of the record (struct/union)
  slang::MayValue fieldDtEid;
  std::string fieldName;
  for (auto it = recordDecl->decls_begin(); it != recordDecl->decls_end();
       ++it) {
    uint64_t fieldKey = (uint64_t)(*it);
    spir::BitEntityInfo bitEntityInfo;

    if (isa<RecordDecl>(*it)) {
      fieldDtEid = convertClangRecordTypeBit(cast<RecordDecl>(*it), fieldKey);
      if (fieldDtEid.errorCode) {
        return fieldDtEid;
      }
      fieldName = stu.bittu.datatypes().at(fieldDtEid.value).typename_();
      bitEntityInfo.set_loc_line(stu.bittu.datatypes().at(fieldDtEid.value).loc_line());
      bitEntityInfo.set_loc_col(stu.bittu.datatypes().at(fieldDtEid.value).loc_col());

    } else if (isa<FieldDecl>(*it)) {
      const FieldDecl *fieldDecl = cast<FieldDecl>(*it);
      bool anonymous = false;

      if (fieldDecl->getNameAsString() == "") {
        anonymous = true;
        fieldName = ::slang::Util::getNextUniqueIdStr() + "a";
      } else {
        anonymous = false;
        fieldName = fieldDecl->getNameAsString();
      }

      if (anonymous) {
        fieldDtEid = convertClangRecordTypeBit(nullptr, fieldKey);
        if (fieldDtEid.errorCode) {
          return fieldDtEid;
        }
      } else if (fieldDecl->getType()->isRecordType()) {
        auto type = fieldDecl->getType();
        auto fieldTypeKey = (uint64_t)type.getTypePtr();
        const RecordDecl *rdecl;
        if (type->isStructureType()) {
          rdecl = type->getAsStructureType()->getDecl();
        } else if (type->isUnionType()) {
          rdecl = type->getAsUnionType()->getDecl();
        } else {
          return slang::MayValue(ERR(201));
        }
        fieldDtEid = convertClangRecordTypeBit(rdecl, fieldTypeKey);
        if (fieldDtEid.errorCode) {
          return fieldDtEid;
        }

      } else {
        fieldDtEid = convertClangTypeBit(fieldDecl->getType());
        if (fieldDtEid.errorCode) {
          return fieldDtEid;
        }
      }
      SrcLoc fieldSrcLoc = getSrcLocBit(fieldDecl);
      bitEntityInfo.set_loc_line(fieldSrcLoc.line);
      bitEntityInfo.set_loc_col(fieldSrcLoc.col);
    }

    bitEntityInfo.set_ekind(spir::K_EK::ERECORD_FIELD);
    bitEntityInfo.set_eid(fieldKey);
    bitEntityInfo.set_parenteid(typeKey);
    bitEntityInfo.set_datatypeeid(fieldDtEid.value);
    bitEntityInfo.set_strval(fieldName);
    stu.bittu.mutable_entityinfo()->emplace(fieldKey, bitEntityInfo);

    dt.mutable_fopids()->Add(fieldKey);
    dt.mutable_foptypeeids()->Add(fieldDtEid.value);
  } // for loop

  // Place the record type with complete fields information in the
  // BitTU.datatypes map.
  stu.bittu.mutable_datatypes()->emplace(typeKey, dt);

  // store for later use (part-of-hack1))
  lastAnonymousRecordDecl = recordDecl;

  return slang::MayValue(OK, typeKey);
} // convertClangRecordTypeBit()

std::string slang::SpirGen::convertClangArrayType(QualType qt) {
  std::stringstream ss;

  const Type *type = qt.getTypePtr();
  const ArrayType *arrayType = type->getAsArrayTypeUnsafe();

  if (isa<ConstantArrayType>(arrayType)) {
    ss << "types.ConstSizeArray(of=";
    ss << convertClangType(arrayType->getElementType());
    ss << ", ";
    auto constArrType = cast<ConstantArrayType>(arrayType);
    auto size = constArrType->getSize();
    charSv->clear();
    size.toString(*charSv, 10, false);
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

slang::MayValue slang::SpirGen::convertClangArrayTypeBit(QualType qt,
                                                  const uint64_t typeKey) {
  spir::BitDataType dt;
  dt.set_typeid_(typeKey);

  const Type *type = qt.getTypePtr();
  const ArrayType *arrayType = type->getAsArrayTypeUnsafe();

  if (isa<ConstantArrayType>(arrayType)) {
    dt.set_vkind(spir::K_VK::TARR_FIXED);
    auto constArrType = cast<ConstantArrayType>(arrayType);
    auto size = constArrType->getSize();
    // Convert llvm::APInt to uint32_t safely
    uint64_t sizeVal = size.getLimitedValue(UINT32_MAX);
    if (sizeVal > UINT32_MAX) {
      SLANG_FATAL("Array size too large");
      return slang::MayValue(ERR(106));
    }
    dt.set_len(static_cast<uint32_t>(sizeVal));
  } else if (isa<VariableArrayType>(arrayType)) {
    dt.set_vkind(spir::K_VK::TARR_VARIABLE);
  } else if (isa<IncompleteArrayType>(arrayType)) {
    dt.set_vkind(spir::K_VK::TARR_PARTIAL);
  } else {
    SLANG_FATAL("Unknown array type");
    return slang::MayValue(ERR(105));
  }

  slang::MayValue elemType = convertClangTypeBit(arrayType->getElementType());
  if (elemType.errorCode) {
    return elemType;
  }
  dt.set_subtypeeid(elemType.value);

  stu.bittu.mutable_datatypes()->emplace(typeKey, dt);

  return slang::MayValue(OK, typeKey);
} // convertClangArrayTypeBit()

std::string slang::SpirGen::convertFunctionPrototype(QualType qt) {
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

slang::MayValue slang::SpirGen::convertFunctionPrototypeBit(QualType qt,
                                                     const uint64_t typeKey) {
  spir::BitDataType dt;
  dt.set_typeid_(typeKey);
  dt.set_funcprototype(true);

  const Type *funcTypePtr = qt.getTypePtr()->getUnqualifiedDesugaredType();

  if (isa<FunctionProtoType>(funcTypePtr)) {
    auto funcProtoType = cast<FunctionProtoType>(funcTypePtr);

    // STEP 1: Convert the return type.
    auto retTypeResult = convertClangTypeBit(funcProtoType->getReturnType());
    if (retTypeResult.errorCode) {
      return retTypeResult;
    }
    dt.set_subtypeeid(retTypeResult.value);
    dt.set_vkind(stu.bittu.datatypes().at(retTypeResult.value).vkind());

    // STEP 2: Convert the parameters one by one.
    for (auto qType : funcProtoType->getParamTypes()) {
      auto paramTypeResult = convertClangTypeBit(qType);
      if (paramTypeResult.errorCode) {
        return paramTypeResult;
      }
      dt.mutable_foptypeeids()->Add(paramTypeResult.value);
    }

    // STEP 3: Special variadic flag.
    if (funcProtoType->isVariadic()) {
      dt.set_variadic(true);
    }

  } else {
    SLANG_FATAL("Unknown function prototype type.");
    return slang::MayValue(ERR(112));
  }

  stu.bittu.mutable_datatypes()->emplace(typeKey, dt);
  return slang::MayValue(OK, typeKey);
} // convertFunctionPrototypeBit()

std::string slang::SpirGen::convertFunctionPointerType(QualType qt) {
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
slang::MayValue slang::SpirGen::convertFunctionPointerTypeBit(QualType qt,
                                                       const uint64_t typeKey) {
  slang::MayValue result;

  spir::BitDataType dt;
  dt.set_vkind(spir::K_VK::TPTR_TO_FUNC);
  dt.set_typeid_(typeKey);

  const Type *typePtr = qt.getTypePtr();
  const Type *funcTypePtr = typePtr->getPointeeType().getTypePtr();
  const Type *unqualifiedPtr = funcTypePtr->getUnqualifiedDesugaredType();

  if (isa<FunctionProtoType>(unqualifiedPtr)) {
    result = convertFunctionPrototypeBit(qt, (uint64_t)unqualifiedPtr /*key*/);
    if (result.errorCode) {
      return result;
    }
    dt.set_subtypeeid(result.value);
    stu.bittu.mutable_datatypes()->emplace(typeKey, dt);
    return slang::MayValue(OK, typeKey);

  } else if (isa<FunctionNoProtoType>(unqualifiedPtr)) {
    // With no function prototype, assume int32 return type with no parameters
    dt.set_subtypeeid(K_00_INT32_TYPE_EID); // i.e. INT32 -- implying `int32 f(void)`
    stu.bittu.mutable_datatypes()->emplace(typeKey, dt);
    return slang::MayValue(OK, typeKey);

  } else if (isa<FunctionType>(unqualifiedPtr)) {
    SLANG_FATAL("A FuncType -- not expected");
    return slang::MayValue(ERR(110));

  } else {
    SLANG_FATAL("Unknown function pointer type");
    return slang::MayValue(ERR(111));
  }

} // convertFunctionPointerTypeBit()

// FIXME:
spir::BitEntity slang::SpirGen::convertClangTypeToBitEntity(QualType qt,
                                                       uint64_t eid) {
  spir::BitEntity bitEntity;
  bitEntity.set_eid(eid);

  spir::BitEntityInfo *bitEntityInfo = convertClangTypeToBitEntityInfo(qt, eid);
  stu.moveAndAddBitEntityInfo(eid, *bitEntityInfo);

  return bitEntity;
} // convertClangTypeToBitEntity()

// FIXME:
spir::BitEntityInfo *
slang::SpirGen::convertClangTypeToBitEntityInfo(QualType qt, uint64_t eid) {
  spir::BitEntityInfo *bitEntityInfo = new spir::BitEntityInfo();
  bitEntityInfo->set_eid(eid);
  bitEntityInfo->set_ekind(spir::K_EK::EDATA_TYPE);
  spir::BitDataType *bitDataType = new spir::BitDataType();
  convertClangTypeBit(qt);
  if (stu.isBasicBitType(
          bitDataType)) { // Call the member function instead of inline check
    bitEntityInfo->set_vkind(bitDataType->vkind());
    //FIXME bitEntityInfo->set_qtype(bitDataType->qtype());
    delete bitDataType;
  } else {
    //FIXME bitEntityInfo->set_allocated_dt(bitDataType);
  }
  return bitEntityInfo;
} // convertClangTypeToBitEntityInfo()

// BOUND END  : type_conversion_routines
// BOUND END  : conversion_routines

// BOUND START: helper_routines

slang::SlangExpr slang::SpirGen::genTmpVariable(std::string suffix,
                                         std::string typeStr,
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
  // FIXME: The var's 'id' here should be small enough to not interfere with
  // uint64_t addresses.
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

// Generates a temporary (proto bit) variable with the given type and suffix.
// It creates BitEntity and spir::BitEntityInfo objects, saves the info object
// and returns the BitEntity object.
spir::BitEntity slang::SpirGen::genTmpBitEntity(
    spir::K_VK vType, std::string suffix, SrcLoc srcLoc,
    QualType qt/*optional if vType is given*/) {
  spir::BitEntity bitEntity;

  // STEP 1: Populate an entity with unique ID.
  bitEntity.set_eid(stu.nextUniqueId());
  bitEntity.set_line(srcLoc.line);
  bitEntity.set_col(srcLoc.col);

  // STEP 2: Create and populate the spir::BitEntityInfo object.
  spir::BitEntityInfo bitEntityInfo;
  bitEntityInfo.set_eid(bitEntity.eid());
  bitEntityInfo.set_ekind(spir::K_EK::EVAR_LOCL_TMP); // All tmps are local variables
  // STEP 2.1: Set the data type to the entity info.
  if (!qt.isNull()) {
    slang::MayValue dt = convertClangTypeBit(qt);
    if (dt.errorCode) {
      SLANG_FATAL("Couldn't convert the clang type " << qt.getAsString())
    }
    bitEntityInfo.set_datatypeeid(dt.value);
    bitEntityInfo.set_vkind(stu.bittu.datatypes().at(dt.value).vkind());
  } else {
    bitEntityInfo.set_vkind(vType);
  }
  bitEntityInfo.set_loc_line(bitEntity.line());
  bitEntityInfo.set_loc_col(bitEntity.col());

  // STEP 2.2: Populate the BitEntityInfo object with a unique name.
  std::stringstream ss;
  ss << "" << stu.nextTmpId() << suffix;
  bitEntityInfo.set_strval(ss.str());

  // STEP 3: Add the variable to the TU.
  // FIXME: The var's 'id' here should be small enough to not interfere with
  // uint64_t addresses.
  stu.bittu.mutable_entityinfo()->emplace(bitEntityInfo.eid(), bitEntityInfo);

  return bitEntity;
} // genTmpBitEntity()

slang::SlangExpr slang::SpirGen::genTmpVariable(std::string suffix, QualType qt,
                                         std::string locStr, bool ifTmp) {
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
  // FIXME: The var's 'id' here should be small enough to not interfere with
  // uint64_t addresses.
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

// Remove qualifiers and typedefs
QualType slang::SpirGen::getCleanedQualType(QualType qt) {
  if (qt.isNull())
    return qt;
  qt = qt.getCanonicalType();
  qt.removeLocalConst();
  qt.removeLocalRestrict();
  qt.removeLocalVolatile();
  return qt;
}

void slang::SpirGen::addGotoInstr(const std::string &label) {
  std::stringstream ss;
  ss << "instr.GotoI(\"" << label << "\")";
  stu.addStmt(ss.str());
}

void slang::SpirGen::addNopBitInstr(const NullStmt *nullStmt) {
  spir::BitInsn *bitInsn = new spir::BitInsn();
  bitInsn->set_ikind(spir::K_IK::INOP);
  bitInsn->set_loc_line(getSrcLocBit(nullStmt).line);
  bitInsn->set_loc_col(getSrcLocBit(nullStmt).col);
  stu.addStmtBit(bitInsn);
}


// Creates and adds a GOTO instruction as a BitInsn to the current statement
// list.
void slang::SpirGen::addGotoInstrBit(spir::BitEntity labelBit, SrcLoc srcLoc) {
  spir::BitInsn *insn = new spir::BitInsn();
  insn->set_ikind(spir::K_IK::IGOTO);      // Set the instruction kind to GOTO
  insn->set_loc_line(srcLoc.line); // Set source location line
  insn->set_loc_col(srcLoc.col);   // Set source location column

  spir::BitExpr *bExpr =
      createBitExpr(labelBit); // Create the expression for the label entity
  insn->set_allocated_expr1(
      bExpr); // Attach label expression to insn (destination)

  stu.addStmtBit(insn); // Add the instruction to stmt bit stream
} // addGotoInstrBit()

void slang::SpirGen::addLabelInstrBit(spir::BitEntity labelBit, SrcLoc srcLoc) {
  // This method adds a label instruction as a BitInsn to the current Bit
  // statement stream.
  spir::BitInsn *insn = new spir::BitInsn();
  insn->set_ikind(spir::K_IK::ILABEL);     // Set instruction kind to LABEL
  insn->set_loc_line(srcLoc.line); // Set source location line
  insn->set_loc_col(srcLoc.col);   // Set source location column

  spir::BitExpr *bExpr = createBitExpr(labelBit); // Create label bit expression
  insn->set_allocated_expr1(bExpr);         // Attach label to the instruction

  stu.addStmtBit(insn); // Add the BitInsn to the bit statement stream
} // addLabelInstrBit()

void slang::SpirGen::addLabelInstr(const std::string &label) {
  std::stringstream ss;
  ss << "instr.LabelI(\"" << label << "\")";
  stu.addStmt(ss.str());
}

void slang::SpirGen::addLabelInstrBit(spir::BitEntity label) {
  spir::BitInsn *insn = new spir::BitInsn();
  insn->set_ikind(spir::K_IK::ILABEL);
  insn->set_loc_line(label.line());
  insn->set_loc_col(label.col());
  spir::BitExpr *bExpr = createBitExpr(label);
  insn->set_allocated_expr1(bExpr);
  stu.addStmtBit(insn);
}

// Create BitEntityInfo for the label, saves it and return its spir::BitEntity.
// FIXME: use same label id within a function (use a map for each function).
spir::BitEntity slang::SpirGen::createLabelBit(std::string name, SrcLoc srcLoc) {
  // Step 1: Create a new BitEntityInfo for the label.
  spir::BitEntityInfo labelInfo;
  // Generate a unique entity id for the label (using stu's unique id scheme).
  uint64_t eid = stu.getLabelId(name);
  labelInfo.set_eid(eid);
  labelInfo.set_ekind(spir::K_EK::ELABEL);
  // Set the label's name as strVal, and source location.
  labelInfo.set_strval(name);
  labelInfo.set_loc_line(srcLoc.line);
  labelInfo.set_loc_col(srcLoc.col);

  // Step 2: Save this spir::BitEntityInfo (assuming stu.addBitEntity is the right
  // owner).
  stu.bittu.mutable_entityinfo()->emplace(eid, labelInfo);

  // Step 3: Return the label's eid as the "address".
  spir::BitEntity be;
  be.set_eid(eid);
  be.set_line(srcLoc.line);
  be.set_col(srcLoc.col);
  return be;
}

void slang::SpirGen::addCondInstr(std::string expr, std::string trueLabel,
                                  std::string falseLabel, std::string locStr) {
  std::stringstream ss;
  ss << "instr.CondI(" << expr;
  ss << ", \"" << trueLabel << "\"";
  ss << ", \"" << falseLabel << "\"";
  ss << ", " << locStr << ")";
  stu.addStmt(ss.str());
}

void slang::SpirGen::addCondInstrBit(SlangBitExpr expr, spir::BitEntity trueLabel,
                                     spir::BitEntity falseLabel, SrcLoc srcLoc) {
  assert(!expr.compound);

  spir::BitInsn *insn = new spir::BitInsn();
  insn->set_ikind(spir::K_IK::ICOND);
  insn->set_allocated_expr1(expr.cloneBitExpr());

  // Create an expression with true and false labels.
  // Set the true label as operand1 and the false label as operand2.
  spir::BitExpr *bExpr = createBitExpr(spir::K_XK::XVAL, trueLabel, falseLabel, srcLoc);
  insn->set_allocated_expr2(bExpr); // `delete bExpr;` not required

  insn->set_loc_line(srcLoc.line);
  insn->set_loc_col(srcLoc.col);

  stu.addStmtBit(insn);
}

void slang::SpirGen::addAssignInstr(SlangExpr &lhs, SlangExpr rhs,
                                    std::string locStr) {
  std::stringstream ss;
  if (lhs.compound && rhs.compound) {
    rhs = convertToTmp(rhs); // staticLocal init will not generate tmp
  }
  ss << "instr.AssignI(" << lhs.expr;
  ss << ", " << rhs.expr << ", " << locStr << ")";
  stu.addStmt(ss.str());
}

void slang::SpirGen::addAssignBitInstr(SlangBitExpr lhs, SlangBitExpr rhs) {
  bool tmpRhs = false;
  // STEP 1: Make sure it remains a 3-address-code assignment (i.e. only one
  // op).
  if (lhs.compound && rhs.compound) {
    rhs = convertToTmpBitExpr(rhs);
    tmpRhs = true;
  }

  // STEP 2: Set the type of assignment instruction.
  spir::BitInsn *bitInsn = new spir::BitInsn();
  if (lhs.compound) {
    bitInsn->set_ikind(spir::K_IK::IASGN_LHS_OP);
  } else if (rhs.compound) {
    if (isBitExprCall(rhs.bitExpr)) {
      bitInsn->set_ikind(spir::K_IK::IASGN_CALL);
    } else {
      bitInsn->set_ikind(spir::K_IK::IASGN_RHS_OP);
    }
  } else {
    bitInsn->set_ikind(spir::K_IK::IASGN_SIMPLE);
  }

  // STEP 3: Set the lhs, rhs and location.
  bitInsn->set_allocated_expr1(lhs.cloneBitExpr());
  bitInsn->set_allocated_expr2(rhs.cloneBitExpr());
  bitInsn->set_loc_line(lhs.bitExpr->loc_line());
  bitInsn->set_loc_col(lhs.bitExpr->loc_col());
  if (tmpRhs) {
    // This rhs is a temporary created in this function,
    // hence we know there is no other use, and we can delete the object.
    rhs.deleteBitExpr();
  }
  stu.addStmtBit(bitInsn);
} // addAssignBitInstr()

bool slang::SpirGen::isBitExprCall(spir::BitExpr *be) {
  return be->xkind() == spir::K_XK::XCALL;
}

bool slang::SpirGen::isBitExprCompound(spir::BitExpr *be) {
  if (be->xkind() == spir::K_XK::XVAL) {
    return false;
  } else {
    return true;
  }
}

// Note: unlike createBinaryExpr, createUnaryExpr doesn't convert its expr to
// tmp expr.
slang::SlangExpr slang::SpirGen::createUnaryExpr(std::string op, SlangExpr expr,
                                          std::string locStr, QualType qt) {
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

// Note: unlike createBinaryExpr, createUnaryExpr doesn't convert its expr to
// tmp expr. It reuses the BitExpr object, and returns the same object.
slang::SlangBitExpr slang::SpirGen::createUnaryBitExpr(spir::K_XK opKind, SlangBitExpr expr,
                                                SrcLoc srcLoc, QualType qt) {
  // Assumes that the oprnd1 is already set correctly.
  expr.bitExpr->set_xkind(opKind);
  expr.bitExpr->set_loc_line(srcLoc.line);
  expr.bitExpr->set_loc_col(srcLoc.col);

  expr.qualType = qt;
  expr.compound = opKind == spir::K_XK::XVAL ? false : true;

  return expr;
} // createUnaryBitExpr()

slang::SlangExpr slang::SpirGen::createBinaryExpr(SlangExpr lhsExpr, std::string op,
                                           SlangExpr rhsExpr,
                                           std::string locStr, QualType qt) {
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

slang::SlangBitExpr slang::SpirGen::createBinaryBitExpr(SlangBitExpr opr1, spir::K_XK op,
                                                 SlangBitExpr opr2,
                                                 SrcLoc srcLoc,
                                                 QualType qt) {
  // Convert the operands to simple expression (if they are not)
  SlangBitExpr leftOpr = convertToTmpBitExpr(opr1);
  SlangBitExpr rightOpr = convertToTmpBitExpr(opr2);

  SlangBitExpr sbExpr;
  sbExpr.qualType = qt;
  sbExpr.bitExpr = new spir::BitExpr();
  sbExpr.compound = true;

  // Set operator
  sbExpr.bitExpr->set_xkind(op);

  // Set left operand and source location
  sbExpr.bitExpr->set_oprnd1eid(leftOpr.bitExpr->oprnd1eid());
  sbExpr.bitExpr->set_oprnd1_line(leftOpr.bitExpr->oprnd1_line());
  sbExpr.bitExpr->set_oprnd1_col(leftOpr.bitExpr->oprnd1_col());

  // Set right operand and source location
  sbExpr.bitExpr->set_oprnd2eid(rightOpr.bitExpr->oprnd1eid());
  sbExpr.bitExpr->set_oprnd2_line(rightOpr.bitExpr->oprnd1_line());
  sbExpr.bitExpr->set_oprnd2_col(rightOpr.bitExpr->oprnd1_col());

  // Set source location
  sbExpr.bitExpr->set_loc_line(srcLoc.line);
  sbExpr.bitExpr->set_loc_col(srcLoc.col);

  return sbExpr;
} // createBinaryBitExpr()

// If the expression is the child of an implicit cast,
// the type of implicit cast is returned, else the given qt is returned
QualType slang::SpirGen::getImplicitType(const Stmt *stmt, QualType qt) {
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
bool slang::SpirGen::isTopLevel(const Stmt *stmt) {
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
        return ((uint64_t)then_ == (uint64_t)stmt ||
                (uint64_t)else_ == (uint64_t)stmt);
      }
      }
    } else {
      return false;
    }
  } else {
    return true; // top level
  }
} // isTopLevel()

slang::SlangExpr
slang::SpirGen::addAndReturnSizeOfInstrExpr(SlangExpr tmpElementVarArr) {
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

////////////////////////////////////////////////////////////////
// BOUND START: the_ast_visitors
////////////////////////////////////////////////////////////////

namespace slang {

class FuncVisitor : public RecursiveASTVisitor<FuncVisitor> {
public:
  explicit FuncVisitor(slang::SpirGen *irgen) : irgen(irgen) {
    // Initialize any other members here if needed
  }

  bool VisitFunctionDecl(FunctionDecl *FD) {
    llvm::outs() << "Found function: " << FD->getNameAsString() << "\n";
    irgen->handleFunctionDecl(FD);
    return true;
  }

private:
  // This irgen and SlangASTConsumer::irgen are aliases.
  SpirGen *irgen;
};

class SlangASTConsumer : public ASTConsumer {
public:
  // Main Entry point for the ASTConsumer (entrypoint for the Slang tool)
  void HandleTranslationUnit(ASTContext &Context) override {
    this->irgen = new slang::SpirGen(&Context);
    Visitor = new FuncVisitor(irgen);

    llvm::outs() << "SlangASTConsumer: \n";

    // Initialize the generator: TU name, out file name etc.
    irgen->slangInit(Context.getTranslationUnitDecl());

    // Handle global variables and inits
    irgen->handleGlobalInits(Context.getTranslationUnitDecl());

    // Handle function declarations and definitions
    // For every function declaration it visits FuncVisitor::VisitFunctionDecl()
    Visitor->TraverseDecl(Context.getTranslationUnitDecl());

    // Perform final actions
    irgen->checkEndOfTranslationUnit(Context.getTranslationUnitDecl());
  }

private:
  FuncVisitor *Visitor;
  // This irgen and SlangASTConsumer::irgen are aliases.
  SpirGen *irgen;
};

class ASTAction : public ASTFrontendAction {
public:
  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &CI,
                                                 StringRef file) override {
    return std::make_unique<SlangASTConsumer>();
  }
};

} // namespace slang

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
  for (const auto &sourcePath : OptionsParser.getSourcePathList()) {
    llvm::outs() << "Processing source file: " << sourcePath << "\n";
  }

  // If using a compilation database, also print compilation info
  if (!OptionsParser.getCompilations().getAllCompileCommands().empty()) {
    llvm::outs()
        << "Using compilation database with "
        << OptionsParser.getCompilations().getAllCompileCommands().size()
        << " entries\n";

    // Print command for each source file we're processing
    for (const auto &sourcePath : OptionsParser.getSourcePathList()) {
      auto compileCommands =
          OptionsParser.getCompilations().getCompileCommands(sourcePath);
      for (const auto &command : compileCommands) {
        llvm::outs() << "  File: " << command.Filename << "\n";
        llvm::outs() << "  Directory: " << command.Directory << "\n";
        llvm::outs() << "  Command: ";
        for (const auto &arg : command.CommandLine) {
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

  // Run our FrontendAction: it eventually calls the HandleTranslationUnit() function.
  int success = Tool.run(newFrontendActionFactory<slang::ASTAction>().get());

  google::protobuf::ShutdownProtobufLibrary();
  return success;
}