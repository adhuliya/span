// RUN: echo '[{"directory": "%S", "command": "gcc hello_world.c -o hello_world", "file": "hello_world.c"}]' > %t.json
// RUN: %slang -p %t.json %s -o %t.py

#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}

// CHECK: name: "hello-world.c"
// CHECK: functions {
// CHECK:   name: "main"
// CHECK:   is_variadic: false
// CHECK: }