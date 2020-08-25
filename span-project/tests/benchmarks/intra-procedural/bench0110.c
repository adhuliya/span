int cond;
int main() {
  int a, *u, tmp, b;
  a = 11;
  b = 13;
  cond = 10;
  u = &a;

  while(cond > 1) {
    tmp = *u;
    b = tmp % 2;
    if(b) {
      b = 15;
    } else {
      b = 16; // unreachable
    }
    u = &b;
    cond += 1;
  }
  return b; // b is 15 here
}
