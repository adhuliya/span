// span idemand /+PointsToA~ConstA/ main <thisfile>
int main()
{
  int a, b, i;
  a = 0;
  b = 20;
  for(i=0;i<b;) {
    if(a)
      b = 10;
    else
      b = 0;
  }
  return b;
}
