int a = 10;
int b = 20;


void f(int c) {
  b = c;
}

int main() {
  a = 30;
  f(100);
  f(100);
  f(100);
  return b;
}
