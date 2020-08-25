int main(int argc, char **argv) {
  int a, *u, tmp, b;
  a = 11;
  b = 13;
  u = &a;

  while(argc > 0) {
    tmp = *u;
    if(tmp) {
      b = 15;
    } else {
      b = 16; // unreachable
    }
    u = &b;
    argc -= 1;
  }
  return b; // b is 15 here
}
