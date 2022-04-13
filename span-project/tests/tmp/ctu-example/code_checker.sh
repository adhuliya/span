#!/usr/bin/env bash

echo "Note: clang must be in the path";

make clean;

CodeChecker log --build "make" --output ./compile_commands.json;

CodeChecker analyze ./compile_commands.json \
  --ctu \
  --capture-analysis-output \
  --output ./reports-ctu \
; # end of command
#  --enable sensitive \

CC=cc CXX=g++ \
   cmake -G Ninja \
     -DCMAKE_EXPORT_COMPILE_COMMANDS=On \
     -DBUILD_SHARED_LIBS=On \
     -DLLVM_ENABLE_ASSERTIONS=On \
     -DLLVM_TARGETS_TO_BUILD="X86" \
     -DLLVM_ENABLE_SPHINX=Off \
     -DLLVM_ENABLE_THREADS=On \
     -DLLVM_INSTALL_UTILS=On \
     -DCMAKE_BUILD_TYPE=Debug \
     ../llvm
