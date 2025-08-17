// RUN: echo '[{"directory": "%S", "command": "gcc hello_world.c -o hello_world", "file": "hello_world.c"}]' > %T/compile_commands.json
// RUN: %dslang -p %T/compile_commands.json %s -proto -o %T
// RUN: %protoc --decode=spir.BitTU --proto_path %S/../../span/pkg/spir/ spir.proto < %T/hello_world.c.spir 2>&1 | %FileCheck %s

int main() {
    return 0;
}

// CHECK: name: "hello_world.c"
// CHECK: {{directory: "/.*/slang/test.*"}}
// CHECK: {{origin: "Clang AST .*clang version [0-9]+\.[0-9]+\.[0-9]+}}