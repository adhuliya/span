// Contributed by Ronak
// Clang/Gcc are unable to optimize this function
// possibly due to fixed cascading sequence
int example_func_1(int a) {
  int b, c, d;

  if (a > 5) {
      c = a % 20;
      b = 90;
  } else {
      c = a % 10;
      b = 100;
  }               //  c in range [0, 19]
                  //  b in range [90, 100] 
  d = c + b;      //  hence d in range [90, 119];
  
  if (d) {        //  so this is always true
      c = 200;
  }               //  hence c is always 200

  return c;
}
