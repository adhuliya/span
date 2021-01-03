int *p = 0;
int g = 0;

void f1(int i) {
  *p = i;
  g++;
}

int main() {
  int a, b, c;
  p = &a;
  c = 10;
  while(--c) {
    f1(c);
  }
  a = 5;
  f1(11);
  b = a;
  return a;
}

