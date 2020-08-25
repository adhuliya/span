// span idemand /+ConstA+PointsToA/s test.c
int main()
{
  int a, b, *p ,*q;
  p = &a;
  q = &b;
  *p = 10;
  *q = 20;
  return a;
}
