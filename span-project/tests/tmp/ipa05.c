int a = 10;
int b = 20;


void f(int c) {
  b = c;
}

int main(int argc, char** argv) {
  a = 30;
  while (argc--) {
    f(100); // look: b is getting ipa-widened here
  }
  return b; // b is (20, 100)
}
