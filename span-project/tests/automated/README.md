SPAN TEST CASES
====================

Note
--------------
Run `./clean` to clean temporary files created during testing.

Test Cases
--------------
This folder contains test cases:

`spanTestXXX.c` is a test C program and its corresponding `spanTestXXX.c.results.py`
contains a list of specially defined python objects that
describe the correct result on a particular action (like 'analyze' or 'c2spanir')
SPAN should have when run on `spanTestXXX.c`.

1. `spanTest001.c` to `spanTest0049.c`
   * without #includes and mallocs
   * without arrays
   * without structs
   * without unions
   * without calls

2. `spanTest050.c` to `spanTest099.c`
   * without #includes and mallocs
   * without structs
   * without unions
   * without calls

3. `spanTest100.c` to `spanTest149.c`
   * without #includes and mallocs
   * without calls

4. `spanTest150.c` to `spanTest199.c`
   * without #includes and mallocs

5. `spanTest200.c` to `spanTest249.c`
   * all features

6. `spanTest400.c` to `spanTest499.c`
   * compound test cases (used as benchmarks)

Some good testcases
------------------------

* `spanTest010.c`

NOTES
----------------

`clang -O3 spanTest010.c` produces a wrong binary. It converts a terminating
loop into an infinite loop. See `spanTest010.s` generated from 
`clang -O3 -S spanTest010.c`.

