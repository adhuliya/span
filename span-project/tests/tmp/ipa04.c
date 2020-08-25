int a = 10;
int b = 20;

void f(int c) {
  if (c < 100) {
    b = c;
    return;
  }
  f(c-1);
}

int main() {
  a = 30;
  f(100);
  return b;
}
