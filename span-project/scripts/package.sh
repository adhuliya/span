#!/usr/bin/env zsh
# This script creates a copy of the SPAN implementation,
# with the core modules in binary form.

PKG_DIR=span-tool

rm -Rf ./**/__pycache__
rm -Rf $PKG_DIR.tgz $PKG_DIR

# Del all cython files except .py (original)
for FILE in host clients diagnosis; do
  rm -Rf span/sys/*.so;
  rm -Rf span/sys/$FILE.c;
  rm -Rf span/sys/$FILE.html;
done

# IMPORTANT: compile critical source files.
./cython_compile.py build_ext --inplace

mkdir -p $PKG_DIR

cp -r LICENSE main.py README.md span tests $PKG_DIR

# Del all files except .so (in the copy)
for FILE in host clients diagnosis; do
  rm -Rf $PKG_DIR/span/sys/$FILE.py;
  rm -Rf $PKG_DIR/span/sys/$FILE.c;
  rm -Rf $PKG_DIR/span/sys/$FILE.html;
done

# Del all cython files except .py (original)
rm -Rf span/sys/*.so;
for FILE in host clients diagnosis; do
  rm -Rf span/sys/$FILE.c;
  rm -Rf span/sys/$FILE.html;
done

tar -czf $PKG_DIR.tgz $PKG_DIR

