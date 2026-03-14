// test malloc and its type

#include <malloc.h>

int main() {
  char *c;
  double *d;
  void *v;

  c = malloc(20);
  d = malloc(24);

  v = malloc(12);
  c = (char*) v;

  return 0;
}
