typedef struct node {
  int val;
  struct node *next;
} Node;

int main() {
  Node arr[10];
  Node n, n1;
  n.val = 10;
  arr[5].next = &n;
  return arr[5].next->val;
}
