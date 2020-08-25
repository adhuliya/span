// program to test &*x expression

int main() {
  int a, b, *u, *v;
  a = 10;
  b = 20;

  u = &a;
  v = &*u;

  b = *v;

  // it should return value of a (check: echo $?)
  return b; 
}
