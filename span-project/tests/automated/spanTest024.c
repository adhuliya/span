// https://github.com/SVF-tools/Test-Suite/blob/master/complex_tests/test6.c

int main() {
  char a[10];
  char * b ;
  b = a;
  *(b++) = 1;
  return b; // a[] is 1, b points-to a
}

