// Example invocation:
// ./slang test_prog_00.c -p compile_commands.json

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendAction.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "llvm/Support/CommandLine.h"

using namespace clang::tooling;
using namespace llvm;
using namespace clang;

static cl::OptionCategory ToolCategory("slang options");

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
        Visitor.TraverseDecl(Context.getTranslationUnitDecl());
    }
private:
    FunctionVisitor Visitor;
};

class FunctionAction : public ASTFrontendAction {
public:
    std::unique_ptr<ASTConsumer> CreateASTConsumer(
        CompilerInstance &CI, StringRef file) override {
        return std::make_unique<FunctionConsumer>();
    }
};

/*
int main(int argc, const char **argv) {
    if (argc > 1) {
        clang::tooling::runToolOnCode(std::make_unique<FunctionAction>(), argv[1]);
    }
    return 0;
} 
*/

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