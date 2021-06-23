
Get the coremark source:

    git clone git@github.com:eembc/coremark.git


Home: <https://www.eembc.org/coremark/>

To generate the combined source file,

    cd coremark
    # make sure clang and cilly are in path
    export CC="cilly --merge --keepmerged --gcc=clang "
    make

 This will generate `coremark.exe_comb.c` source file.

     clang coremark.exe_comb.c -o a.out;


