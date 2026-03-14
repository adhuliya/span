// Example to check inter-procedural liveness analysis
// and Points-To analyses in action.

int g;
int h = 10;
int *u;
int (*fp)(void);

int gg() {
  int x;
  x = x + g;
  return x;
  // x is live here
}

int ff() {
  int x;
  x = x + h;
  return x;
  // x is live here
}

int main(int argc) {
  if (argc)
    if (argc) 
      fp = 0;
    else
      fp = &gg;
  else
    fp = &ff;
  g = 10;
  g = fp();
  return g;
}

