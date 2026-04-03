
// to test the call graph

int* f(void *x) {
  return (int*)(*((int*)x));
}

void* g(int *x) {
  return x;
}

int main() {
  void* (*fp1)(int*);
  int* (*fp2)(void*);
  int x=1;

  fp1 = g;
  fp2 = f;

  fp1(&x); // call edge from main to f and g
  fp2(&x); // call edge from main to f and g

  return 0;
}
