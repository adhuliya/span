struct Node {
  int val;
  struct Node *next;
};

int main() {
  struct Node n1, n2;
  n1.val = 10;
  n2 = n1; // n2.val should be 10
  return n2.val;
}
