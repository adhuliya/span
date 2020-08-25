// example specially for PointsToA and ConstA
int main(int argc) {
  int a, b, c;
  int *p;
  a = 10;
  b = 20;

  if (a) {
    p = &a;
  } else {
    p = &b;
  }

  c = *p; //p should point to only a
  return c; // value of c is 10
}
