#!/usr/bin/env bash

# Run this file with an argumen *.c.clang.log to check
# the presence of any errors.

grep "ERROR:" $1;
