// Example to check inter-procedural liveness analysis
// and Points-To analyses in action.

int g;
int h = 10;
int *u;


int f() {
  int x;
  // argc, g, h and u are live here
  x = *u;
  x = x + h;
  return x;
  // x is live here
}

int main(int argc) {
  if (argc)
    u = &g;
  else
    u = &argc;
  g = 10;
  // argc, g, h and u are live here
  g = f();
  return g;
}

