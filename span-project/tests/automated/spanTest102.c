// test struct with an array

typedef struct nnode {
  int x;
  int arr[10];
} Node;

int main() {
  Node n, *p;
  int *x;
  p = &n;

  x = p->arr; // x points to n.arr
  return 0;
}
