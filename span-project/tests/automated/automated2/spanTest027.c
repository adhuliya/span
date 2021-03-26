int main() {
  int *p1, *p2;
  int x;
  p1 = &x;
  p2 = p1 + x; // p2 points to x too.

  return 0;
}
