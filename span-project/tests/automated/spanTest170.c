int *p = 0;
int z;

int f1(int i) {
  *p = i;
  if (i == z)
    return *p;
  else
    return z;
}

int main(int argc) {
  int a, b, c;
  z = argc;
  p = &a;
  b = f1(11); //OUT: a is 11, b is Bot
  f1(10); //OUT: a is 10
  return a;
}
