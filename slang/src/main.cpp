// Example invocation:
// ./slang test_prog_00.c -p compile_commands.json

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendAction.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "llvm/Support/CommandLine.h"
#include "util.h"
#include "spir.pb.h"

using namespace clang::tooling;
using namespace llvm;
using namespace clang;

#define GLOBAL_DUMMY_FUNC_NAME "00_global_inits"

static cl::OptionCategory ToolCategory("slang options");

namespace spir {
  BitSrcLoc getSrcLoc(ASTContext &Ctx, const Stmt *stmt) {
    BitSrcLoc loc;

    loc.set_line(Ctx.getSourceManager().getExpansionLineNumber(stmt->getBeginLoc()));
    loc.set_col(Ctx.getSourceManager().getExpansionColumnNumber(stmt->getBeginLoc()));

    return loc;
  }

  BitSrcLoc getSrcLoc(ASTContext &Ctx, const ValueDecl *decl) {
    BitSrcLoc loc;

    loc.set_line(Ctx.getSourceManager().getExpansionLineNumber(decl->getBeginLoc()));
    loc.set_col(Ctx.getSourceManager().getExpansionColumnNumber(decl->getBeginLoc()));

    return loc;
  }

  void handleGlobalInits(ASTContext &Ctx, const TranslationUnitDecl *decl) {
    // All global initializations are stored in a global dummy function
    // as a sequence of statements.
    // This function should be visited only once.

    if (!decl) {
      SLANG_FATAL("TranslationUnitDecl is null");
      return;
    }

    // SlangFunc slangFunc;
    // slangFunc.fullName  = slangFunc.name = GLOBAL_DUMMY_FUNC_NAME;
    // stu.funcMap[0]      = slangFunc;
    // stu.currFunc        = &stu.funcMap[0];   // the special global function

    for (auto it = decl->decls_begin(); it != decl->decls_end(); ++it) {
      const VarDecl *varDecl = dyn_cast<VarDecl>(*it);
      if (varDecl) {
        SLANG_DEBUG("Found global variable: " << varDecl->getNameAsString()
            << " at " << getSrcLoc(Ctx, varDecl).DebugString());
        // handleVarDecl(varDecl);
      }
    }
  } // handleGlobalInits()
}

////////////////////////////////////////////////////////////////
// BOUND START: Top_Level_Visitors
////////////////////////////////////////////////////////////////

class FunctionVisitor : public RecursiveASTVisitor<FunctionVisitor> {
public:
    bool VisitFunctionDecl(FunctionDecl *FD) {
        llvm::outs() << "Found function: " << FD->getNameAsString() << "\n";
        return true;
    }
};

class FunctionConsumer : public ASTConsumer {
public:
    void HandleTranslationUnit(ASTContext &Context) override {
        this->Context = &Context;
        llvm::outs() << "FunctionConsumer: \n";
        spir::handleGlobalInits(Context, Context.getTranslationUnitDecl());
        Visitor.TraverseDecl(Context.getTranslationUnitDecl());
    }
private:
    FunctionVisitor Visitor;
    ASTContext *Context;
};

class FunctionAction : public ASTFrontendAction {
public:
    std::unique_ptr<ASTConsumer> CreateASTConsumer(
        CompilerInstance &CI, StringRef file) override {
        return std::make_unique<FunctionConsumer>();
    }
};

////////////////////////////////////////////////////////////////
// BOUND END: Top_Level_Visitors
////////////////////////////////////////////////////////////////

int main(int argc, const char **argv) {
    // Parse command-line options
    auto ExpectedParser = CommonOptionsParser::create(argc, argv, ToolCategory);
    if (!ExpectedParser) {
        llvm::errs() << ExpectedParser.takeError();
        return 1;
    }
    CommonOptionsParser &OptionsParser = ExpectedParser.get();

    // Set up ClangTool
    ClangTool Tool(OptionsParser.getCompilations(),
                   OptionsParser.getSourcePathList());

    // Run our FrontendAction
    return Tool.run(newFrontendActionFactory<FunctionAction>().get());
}