SPAN Implementation
===================

Synergistic Program ANalysis Implementation.

SPAN is a system built as a framework in Haskell language. Some of its helper system is implemented in Python and C++. It understands its own custom intermediate representation called SPAN IR. The following system functions can be explicitly controlled,

* The main analysis to perform. (as a result all other analyses used are helper analyses)
* Context Sensitive vs. Context Insensitive
* Maximum number of analyses to invoke simultaneously
* Disable specific analyses/ information type.
* Disable a category of expression simplification.

TODOs
---------------

0. Make Hoopl work.
1. IR Type System
2. Abstract SPAN IR
3. (D...) IR Converter : Clang IR to SPAN IR (C++/Python) (done 20 % todo enlist and extract all details)
4. Result Converter : Map & Translate SPAN IR results to Clang IR (C++/Python) [OPTIONAL]
5. Set of toy test programs (`tests/toy/`)
6. Host framework in Haskell.
7. Analysis specification in Haskell.
8. Analysis information sharing (e.g. points-to info: Ptr a -> a).
9. Automated Tests and Result generation (C++/Python)
10. (DONE) Method to Compile benchmarks to single LLVM IR module/translation unit. (done : do for all individual benchmarks) See `/home/codeman/.itsoflife/local/tmp/gcc_spec` and `/home/codeman/.itsoflife/local/tmp/gobmk_spec` folders. The first one has a readme file and build.sh scripts in both the folders build the llvm ir from the code base copied from the spec benchmark. Similar stuff has to be done for other individual benchmarks.
