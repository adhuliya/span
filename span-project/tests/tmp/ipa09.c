int *p = 0;

void f1(int i) {
  if(i)
    *p = i;
  else
    f1(i+1);
}

int main() {
  int a, b, c;
  // a = 5; // make a bot
  p = &a;
  f1(a);
  f1(11);
  b = a;  // a is (11, 11)
  return a;
}

