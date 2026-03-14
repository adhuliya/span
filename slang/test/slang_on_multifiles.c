// Test Slang on multiple files at once. (TODO)
// XFAIL: *

// DEFINE: %{SRC} = test_prog_00.c
// DEFINE: %{CMD} = \
// DEFINE: echo [
// DEFINE:   { \
// DEFINE:    "directory": "%S/src", \
// DEFINE:    "command": "gcc %{SRC} -o %{SRC:.c=.o}", \
// DEFINE:    "file": "%{SRC}" \
// DEFINE:   },
// DEFINE:   { \
// DEFINE:    "directory": "%S/src", \
// DEFINE:    "command": "gcc %{SRC} -o %{SRC:.c=.o}", \
// DEFINE:    "file": "%{SRC}" \
// DEFINE:   } \
// ] > %T/compile_commands.json \
// DEFINE: && %dslang -p %T/compile_commands.json %S/src/%{SRC} -bit-spir -o %T 2>&1 %T/%{SRC}.slang.output

// DEFINE: %{SRC} = test_prog_01.c