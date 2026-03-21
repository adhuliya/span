// Test CFG: switch cases

int main(int argc, char **argv) {
  int x = 4;
  switch(argc) {
    case 1:
      x = x + 1;
    case 2:
      x = x + 2;
      break;
    default:
      x = x + x;
  }
  return x;
}

