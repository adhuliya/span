// Test array approximation and pointer to arrays.


int main() {
  int a[10], b[10], *p;
  a[0] = 11;

  p = a;
  p[1] = 22;

  return a[0]; // a's range is (11, 22)
}
