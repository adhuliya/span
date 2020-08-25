// Command used:
//     span ianalyze /+IntervalA~EvenOddA~PointsToA/ main spanTest021.c
// Since EvenOddA is a supporting analysis and it fails in simplifying
// if condition, it should not process the whole program unnecessarily.

int main() {
  int a, b;
  int* p = &a;
  while(a) {
    b = *p;
    if (b) {
      a = 10;  // EvenOddA will not process this stmt
    } else {
      a = 30;  // EvenOddA will not process this stmt
    }
  }
  return a;
}
