Coreutils Programs v8.24
----------------------

Coreutils download page:
<https://ftp.gnu.org/gnu/coreutils>

Decoding the source code:
<http://www.maizure.org/projects/decoded-gnu-coreutils/>

 
Excluded `tac-pipe.c` as it was not compiling.

Steps used to collect these sources
1. Download <https://ftp.gnu.org/gnu/coreutils/coreutils-8.24.tar.xz>
2. Untar and build the coreutils,

        cd coreutils-8.24;
        ./configure
        ./make

3. If the building is successful preprocess all `*.c` files to `*.c.e.c` names,

        cd coreutils-8.24/src;
        # assuming clang is in source
        for x in *.c; do echo $x; clang -E -I../lib $x -o $x.e.c; done

4. Copy all the `*.c.e.c` files were copied into this directory.
   To check if all the `*.c.e.c` files were compiling we ran,

        for x in *.e.c; do echo $x; clang -c $x -o /dev/null; done 

   In the command `tac-pipe.c` failed hence is excluded from the collection.



