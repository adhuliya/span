// Optimize the if statement


int foo() {
  return 10;
}

int main() {
  int a = foo();
  if (a) {
    return 0;
  } else {
    return 1;
  }
}
