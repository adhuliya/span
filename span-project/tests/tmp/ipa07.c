int *p = 0;

void f1(int i) {
  *p = i;
}

// void f2(int i) {
//   g1 = i;
// }

int main() {
  int a, b;
  p = &a;
  a = 5;
  f1(11);
  b = a;
  // f2(12);
  return a;
}
