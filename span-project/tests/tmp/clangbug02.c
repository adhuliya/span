#include<stdlib.h>

int global;

int foo(int **p) {
  *p = &global; 
}

int main(int argc, char** argv) {
  int *p = (int*)malloc(16);
  foo(&p);
  free(p);
  return argc;
}
