int a = 10;
int b = 20;

void g(int d) {
  a = d;
}

void f(int c) {
  b = c;
  g(200);
}

int main() {
  a = 30;
  f(100);
  return b;
}
