// Example to check inter-procedural liveness analysis

int g;


int f() {
  g = 20;
  return 0;
}

int main() {
  // g is dead here
  f();
  return g;
}
