int main(int argc) {
  int b, y;
  b = 0; // argc shouldn't be live (liveness+cp)
  if (b) {
    y = argc + 2;
  } else {
    y = 20;
  }
  return y;
}
