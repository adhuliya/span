int g1 = 10;

void f1(int i) {
  g1 = i;
}

// void f2(int i) {
//   g1 = i;
// }

int main() {
  int a, b;
  a = 5;
  f1(11);
  b = a;
  // f2(12);
  // a = g1;
  return g1;
}
