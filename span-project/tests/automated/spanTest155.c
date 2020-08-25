// program to test &x->y->z;

struct Record1 {
  int z;
};

struct Record0 {
  struct Record1 *y;
};

int main() {
  struct Record0 r0;
  struct Record1 r1;
  struct Record0 *x;
  int a, *p;

  r0.y = &r1;
  r0.y->z = 20;

  x = &r0;
  p = &x->y->z;

  a = *p;

  return a; // should return 20
}

