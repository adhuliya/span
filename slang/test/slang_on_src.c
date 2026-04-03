// The tests below only test if the slang tool runs without error on the given files.
// These are tests that run on the C sourcefiles in the `test/src` directory.
// Slang tool is run on each of the source files one at a time.

// Q. How are the tests executed?
// A. Tests are run on one source file at a time. For each test file,
//    first the compile_commands.json file is initialized, then the slang invocation is run.


// DEFINE: %{SRC} =
// DEFINE: %{CMD} = \
// DEFINE: echo [{ \
// DEFINE:    \"directory\": \"%S/src\", \
// DEFINE:    \"command\": \"gcc %{SRC} -o %{SRC}\", \
// DEFINE:    \"file\": \"%{SRC}\" \
// DEFINE: }] > %T/compile_commands.json \
// DEFINE: && %dslang -p %T/compile_commands.json %S/src/%{SRC} -bit-spir -out-dir %T \
// DEFINE:    |& tee %T/%{SRC}.slang.output.txt \
// DEFINE: && %protoc --decode=spir.BitTU --proto_path %S/../../span/pkg/spir/ spir.proto < %T/%{SRC}.spir.pb 2>&1 \
// DEFINE:   | tee %T/%{SRC}.spir.pb.txt

// REDEFINE: %{SRC} = spanTest001.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest002.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest004.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest005.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest010.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest012.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest013.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest021.c
// RUN: %{CMD}

// FIXME-- handle array init-list expr later
// REDEFINE- %{SRC} = spanTest022.c
// RUN- %{CMD}

// REDEFINE: %{SRC} = spanTest024.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest025.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest027.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest052.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest102.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest113.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest160.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest161.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest162.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest165.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest166.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest167.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest168.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest169.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest170.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest171.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest172.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest173.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest174.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest203.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest204.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest205.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest206.c
// RUN: %{CMD}

// REDEFINE: %{SRC} = spanTest207.c
// RUN: %{CMD}