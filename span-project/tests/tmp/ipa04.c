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
  return b; // b is 99
}

// 1. int f (int x, int *p) {
// 2.   if (*p < 5) {
// 3.     *p = *p * 2;
// 4.   } else {
// 5.     p = &x;
// 6.     f(x-1, p);
// 7.   }
// 8.   return x;
// 9. }
// 10. int main() {int z=5; return f(5, &z)};
