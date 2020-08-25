// program to test &arr[][] expression

int main() {
  int arr[10][10];
  int *p;

  p = &arr[5][5];
  *p = 11;

  return arr[5][5]; // should return 11
}

