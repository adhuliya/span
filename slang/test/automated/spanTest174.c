int f(int i) {
  if (i<0) return 0;
  return f(--i);
}

int main(int argc) {
  return f(1000000);
}
