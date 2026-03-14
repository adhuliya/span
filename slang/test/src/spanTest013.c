// OOPSLA review challenge example.


int main (
    int argc, // Making 'x' a parameter to approximate it as a bot value.
    char** argv
) {
  int *p;
  int x, y, z;

  x = argc; // like an input (unknown)
  p = 0;
  y = z = 0;
  if (x > 10) {
    if (x < 0) {
      p = &y;   // unreachable identified by the interval analysis
    } else {
      p = &z;
    }
    *p = 1; // assert(y == 0 && z == 1);
  }
                                                                                                
  return z;
}
