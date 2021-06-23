#!/usr/bin/env bash

# Run this file with an argument to check
# the presence of any errors.

#grep "ERROR:" $1;
grep -e "(ERROR|error)" $1;
