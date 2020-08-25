int c;

void f(int a) {
  c = a;
}

int main(int argc, char **argv) {
  if (argc > 2) {
    f(100);
  } else {
    c = 20;
  }
}
