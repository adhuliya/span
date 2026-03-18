// Test use of goto and labels

int main() {
    int a = 10;
    goto end;
    return a;
    end:
    return 0;
}

int foo() {
    goto end;
    return 0;
    end:
    return 1;
}