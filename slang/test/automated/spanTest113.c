
// to test the call graph

int* f(void *x) {
  return *((int*)x);
}

void* g(int *x) {
  return *x;
}

int main() {
  int* (*fp1)(int*);
  int* (*fp2)(void*);
  int x=1;

  fp1 = f;
  fp2 = g;

  fp1(&x); // call edge from main to f and g
  fp2(&x); // call edge from main to f and g

  return 0;
}
