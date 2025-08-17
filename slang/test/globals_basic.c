// RUN: echo '[{"directory": "%S", "command": "gcc globals_basic.c -o globals_basic", "file": "globals_basic.c"}]' > %T/compile_commands.json
// RUN: %dslang -p %T/compile_commands.json %s -proto -o %T
// RUN: %protoc --decode=spir.BitTU --proto_path %S/../../span/pkg/spir/ spir.proto < %T/globals_basic.c.spir 2>&1 | %FileCheck %s

// A simple C program with globals with builtin types.

int global_int = 10;
float global_float = 3.14;
double global_double = 2.71828;
char global_char = 'A';

int main() {
    return 0;
}

// CHECK: name: "globals_basic.c"
// CHECK: directory: "/workspaces/span/slang/test"
// CHECK: origin: "Clang AST Ubuntu clang version 19.1.1 (1ubuntu1~24.04.2)"
// CHECK: entities {
// CHECK:   key: "g:global_char"
// CHECK:   value {
// CHECK:     id: [[CHAR_ID:[0-9]+]]
// CHECK:     loc {
// CHECK:       line: 10
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: entities {
// CHECK:   key: "g:global_double"
// CHECK:   value {
// CHECK:     id: [[DOUBLE_ID:[0-9]+]]
// CHECK:     loc {
// CHECK:       line: 9
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: entities {
// CHECK:   key: "g:global_float"
// CHECK:   value {
// CHECK:     id: [[FLOAT_ID:[0-9]+]]
// CHECK:     loc {
// CHECK:       line: 8
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: entities {
// CHECK:   key: "g:global_int"
// CHECK:   value {
// CHECK:     id: [[INT_ID:[0-9]+]]
// CHECK:     loc {
// CHECK:       line: 7
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: entityInfo {
// CHECK:   key: [[INT_ID]]
// CHECK:   value {
// CHECK:     kind: VAR_GLBL
// CHECK:     id: [[INT_ID]]
// CHECK:     dt {
// CHECK:       kind: INT32
// CHECK:     }
// CHECK:     strVal: "g:global_int"
// CHECK:     loc {
// CHECK:       line: 7
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: entityInfo {
// CHECK:   key: [[FLOAT_ID]]
// CHECK:   value {
// CHECK:     kind: VAR_GLBL
// CHECK:     id: [[FLOAT_ID]]
// CHECK:     dt {
// CHECK:       kind: FLOAT64
// CHECK:     }
// CHECK:     strVal: "g:global_float"
// CHECK:     loc {
// CHECK:       line: 8
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: entityInfo {
// CHECK:   key: [[DOUBLE_ID]]
// CHECK:   value {
// CHECK:     kind: VAR_GLBL
// CHECK:     id: [[DOUBLE_ID]]
// CHECK:     dt {
// CHECK:       kind: FLOAT64
// CHECK:     }
// CHECK:     strVal: "g:global_double"
// CHECK:     loc {
// CHECK:       line: 9
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: entityInfo {
// CHECK:   key: [[CHAR_ID]]
// CHECK:   value {
// CHECK:     kind: VAR_GLBL
// CHECK:     id: [[CHAR_ID]]
// CHECK:     dt {
// CHECK:       kind: UINT8
// CHECK:     }
// CHECK:     strVal: "g:global_char"
// CHECK:     loc {
// CHECK:       line: 10
// CHECK:       col: 1
// CHECK:     }
// CHECK:   }
// CHECK: }
// CHECK: functions {
// CHECK:   id: 1
// CHECK:   name: "f:00_inits:optional,comma,separated,flags"
// CHECK: }