#!/usr/bin/env bash

_FILE="nullderef.output";

for x in *.spanir; do
  echo -e "\n\n\n" &>> $_FILE;
  echo "$x" &>> $_FILE;
  echo -e "\n" &>> $_FILE;
  pypy3 `which span` diagnose NullDerefR all $x &>> $_FILE;
done

