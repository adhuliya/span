// test struct aggregate assignment

struct node {
  int val;
  int level;
};

int main() {
  struct node arr[] = {{1,2}, {2,3}};
  struct node n = {1,2};
  return n.val;
}
