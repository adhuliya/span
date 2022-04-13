#!/usr/bin/env bash

# A command line invocation to generate a merged C file.
# This generates `a.out_comb.c` file.

cilly \
  --merge \
  --keepmerged \
  --noPrintLn \
  --domakeCFG \
  --useLogicalOperators \
  --gcc=clang \
  *.c \
  |& \
  tee output.cilly.txt \
;
#  --commPrintLnSparse \
