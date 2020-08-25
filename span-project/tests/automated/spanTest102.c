typedef struct node {
  int val;
  struct Node *next;
} Node;

int main(int argc, char **argv) {
  int a, tmp;
  Node n1, n2;
  Node *u;
  n1.val = 11;
  n2.val = 13;
  u = &n1;

  while(argc > 0) {
    tmp = u->val;
    n2.val = tmp % 2;
    if(n2.val) {
      n2.val = 15;
    } else {
      n2.val = 16; // unreachable
    }
    u = &n2;
    argc -= 1;
  }
  return n2.val; // n2.val is 15 here
}

