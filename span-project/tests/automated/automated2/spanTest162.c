// This is a check for a specific error that may arise
// when `*p` is simplified to a pointee set. Since
// SPAN doesn't use the NULL pointee in the simplification,
// it can incidently remove the NULL pointee from the data
// flow value (an error). This program checks to see
// that it doesn't happen anymore.
//
// To utilize this example better, add more dimentions to
// the tests.
int *p; // p has a NULL pointee here.

void f() {
  *p = 11; // NULL pointee must not be removed.
}

int main(int argc) {
  int x = 10;
  if (argc) {
    p = &x; // since addr taken, x is considered global.
  }
  f();
  f(); // ValueContext MISS! (since x changes value)
  f(); // ValueContext should be a HIT!
  return 0;
}


