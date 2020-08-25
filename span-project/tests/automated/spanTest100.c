typedef struct node {
  int val;
  struct Node *next;
} Node;

int main() {
  Node n;
  Node n2;
  n.next = &n2;
  return 0;
}
