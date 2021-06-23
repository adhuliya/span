// Test CFG: switch cases

int main(int argc, char **argv) {
  int x = 4;
  switch(argc) {
    case 1:
      x = x + 1;
    default:
      x = x + 2;
  }
  return x;
}

