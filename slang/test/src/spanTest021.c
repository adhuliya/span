// test the static variable initialization

static int j = 20;

void f1() {
  static int i = 10;
  i++;
}

void f2() {
  static int i;// = 10;
  i++;
  j++;
}

void main() {}

