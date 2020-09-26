int foo(int *p) {
  return *p;
}

int main(int argc, char** argv) {
  int *p;
  if (argc > 1) {
    argc = 1;
  } else {
    p = &argc;
  }
  return foo(p);
}
