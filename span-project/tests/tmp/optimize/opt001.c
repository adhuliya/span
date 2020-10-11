// Optimize the if statement


int foo() {
  return 10;
}

int main() {
  int a = foo();
  int c = a;
  int b = a > 5;
  if (a) {
    return 0;
  } else {
    return 1;
  }
}
