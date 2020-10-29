#include <malloc.h>

typedef struct _Node {
  int x;
  int y;
} Node;

int main() {
  int *p = (int*)malloc(sizeof(int));
  Node *n = (Node*)malloc(sizeof(Node));
  return *p;
}
