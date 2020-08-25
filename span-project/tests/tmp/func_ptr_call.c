// using function pointer to see if the call graph is generated correctly

int sum(int a, int b) {
  return a + b;
}

int sub(int a, int b) {
  return a - b;
}

int main() {
  int (*f)(int, int);
  int (*f1)(int, float);
  f = sum;
  return f1(10,20) + f(10,20) + sub(20,10);
}
