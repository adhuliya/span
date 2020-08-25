int main()
{
  int b, i, *p;
  b = 20;
  p = &b;
  for(i=0;i<b;) {
    *p = 0;
  }
  return b;
}
