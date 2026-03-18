int main(int argc) {
    int a = 10;
    if (a > argc) {
        a = 1;
    } else {
        a = 2;
    }
    landhere:
    a = 3;
    return a;
}