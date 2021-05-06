// Taken from Prof. Uday's 2018 CS618 slide (53/57: dfa-motivation.pdf)

// int a; // Making 'a' a global, makes it a constant.

int f(
    int b,
    int a // Making 'a' a parameter to approximate it as a bot value.
) {
  int c;

  c = a%2; // Variable c is in range (-1, 1)
  b = b <= 0 ? b : - b; // Equivalent to: `b = - abs(b);`

  while (b < c)
    b = b+1;

  if (b > 0)
    b = 0;

  return b; // Variable b is in range (-1, 0)
}
