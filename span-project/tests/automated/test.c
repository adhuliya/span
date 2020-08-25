int main() {
  int a = 10;
  int b = 20;
  int *p = 0;

  if (a) {
    b = a;
  } else {
    p = &a;
    a = 20;
  }

  return *p;
}
