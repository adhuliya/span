// structure
#include<stdlib.h>

typedef struct node {
  int val;
  struct node *next;
} Node;

Node* create() {
  return (Node*)malloc(sizeof(Node));
}

void myfree(Node **n) {
  free(*n);
  *n = NULL;
}

int main() {
  Node *n1, *n2;
  n1 = create();
  n2 = create();
  *n2 = *n1;
  myfree(&n1);
  return n2->val;
}
