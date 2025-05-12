int x;

int foo(int a) {
    return a + 1;
}

int main(int argc, char **argv)
{
    int y;
    int z;

    y = 0;
    z = 0;

    if (y == 0) {
        x = foo(1);
    } else {
        x = foo(2);
    }

    return x;
}