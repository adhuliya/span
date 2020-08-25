#include <malloc.h>

struct Node {
  int val;
  struct Node* next;
};

int main() {
  struct Node n1, n2;
  struct Node* head;
  head = (struct Node*)malloc(sizeof(struct Node)* 10);
  head->next = &n1;
  head->next = &n2;
  return 0;
}
