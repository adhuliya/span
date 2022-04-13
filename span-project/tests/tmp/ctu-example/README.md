Reference:

<https://clang.llvm.org/docs/analyzer/user-docs/CrossTranslationUnit.html>

<https://codechecker.readthedocs.io/en/latest/usage/>


    pip3 install codechecker;
    CodeChecker analyze --ctu compile_commands.json -o reports;


Steps:

    make clean;
    mysource clang;
    CodeChecker log --build "make" --output ./compile_commands.json;
    CodeChecker analyze ./compile_commands.json --output ./reports-ctu --enable sensitive --ctu;
