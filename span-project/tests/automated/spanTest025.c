// https://github.com/SVF-tools/Test-Suite/blob/master/complex_tests/test6.c

char * f(char * a) {
   char * b ;

   b = a;
    *(b++) = 1;
   return b;
}

int main (){
    char a[10];
    char * c;

    c = f(a);
    c = f(c);
    c = f(c);
    c = f(c);
    c[9] = 0;
    *c = 0;
    return 0; // a[] is (0,1), c points-to a
}
