// using function pointers

int a = 11;

int f(int (*ff)(void)) {
  return ff();
}

int f1() {
  return 0;
}

int f2() {
  return 100;
}

int main(int argc, char** argv) {
  int b = 10;
  b = f(f1) + f(f2);
  return b;
}
