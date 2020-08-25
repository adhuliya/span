//#include <stdio.h>

int main() {
  int a, *c, *b, **x;
  a = 5;
  c = &a;
  x = &c;
  b = *x;
  return 0;
}
