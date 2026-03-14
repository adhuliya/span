// The tests below only test if the slang tool runs without error on the given files.
// These are tests that run on the C sourcefiles in the `test/src` directory.
// Slang tool is run on each of the source files one at a time.

// Q. How are the tests executed?
// A. Tests are run on one source file at a time. For each test file,
//    first the compile_commands.json file is initialized, then the slang invocation is run.


// DEFINE: %{SRC} =
// DEFINE: %{CMD} = \
// DEFINE: echo [{ \
// DEFINE:    "directory": "%S/src", \
// DEFINE:    "command": "gcc %{SRC} -o %{SRC}", \
// DEFINE:    "file": "%{SRC}" \
// DEFINE: }] > %T/compile_commands.json \
// DEFINE: && %dslang -p %T/compile_commands.json %S/src/%{SRC} -bit-spir -out-dir %T \
// DEFINE:    |& tee %T/%{SRC}.slang.output

// REDEFINE: %{SRC} = spanTest001.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest002.c
// RUN: %{CMD}