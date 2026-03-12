// Example to check inter-procedural liveness analysis

int g;
int h = 10;


int f() {
  int x;
  x = h + g;
  return x;
  // x is live here
}

int main() {
  g = 10;
  // g and h are live here
  g = f();
  return g;
}
