int main() {
  int a, b, c, i, e;
  int *x, *y, **z, **w;

  x = &a;
  y = &b;
  w = &y;

  if (i < 0) {
    z = &x;
  } else {
    z = &y;
  }

  *z = &e;
  *w = &e;
}
