int a = 10;
int b = 20;


void f() {
  b = 40;
}

int main() {
  a = 30;
  f();
  return b;
}
