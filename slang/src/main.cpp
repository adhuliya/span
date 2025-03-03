#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendAction.h"
#include "clang/Tooling/Tooling.h"

using namespace clang;

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

int main(int argc, const char **argv) {
    if (argc > 1) {
        clang::tooling::runToolOnCode(new FunctionAction, argv[1]);
    }
    return 0;
} 