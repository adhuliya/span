// RUN: echo '[{"directory": "%S", "command": "gcc globals_ptr.c -o globals_ptr", "file": "globals_ptr.c"}]' > %T/compile_commands.json
// RUN: %dslang -p %T/compile_commands.json %s -proto -o %T
// RUN: %protoc --decode=spir.BitTU --proto_path %S/../../span/pkg/spir/ spir.proto < %T/globals_ptr.c.spir 2>&1 | %FileCheck %s

// A simple C program with globals with builtin types.

int* global_int;
int** global_int_ptr = &global_int;
float* global_float = 3.14;
float** global_float_ptr = &global_float;
double* global_double;
char* global_char;

int main() {
    return 0;
}
