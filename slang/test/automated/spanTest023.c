// test struct aggregate assignment

struct node {
  int val;
  int level;
};

struct data {
  int data;
  struct node n;
};

int main() {
  struct node arr[] = {{1,2}, {2,3}};
  struct node n = {1,2};
  struct data d;
  d.n.val = 10;
  return n.val;
}
