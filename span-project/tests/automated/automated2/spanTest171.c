// using function pointers

int a = 11;

int f1(int c) {
  a = c * 2;
  return a;
}

int f2(int d) {
  a = d * 3;
  return a;
}

int main(int argc, char** argv) {
  int b = 10;
  int (*f)(int);
  f = argc ? *f1 : &f2;
  b = f(b);
  return b; // a and b are (20, 30)
}
