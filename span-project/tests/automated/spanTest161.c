int a = 10;
int b = 20;


void f(int c) {
  b = c;
}

int main() {
  a = 30;
  f(100); // b is 100, a is 30
  f(100); // b is 100, a is 30
  f(100); // b is 100, a is 30
  return b; // b is 100, a is 30
}
