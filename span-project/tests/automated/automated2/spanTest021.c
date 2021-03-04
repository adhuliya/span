// test the static variable initialization

void f1() {
  static int i = 10;
  i++;
}

void f2() {
  static int i;// = 10;
  i++;
}

void main() {}

