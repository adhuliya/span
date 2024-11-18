SPAN Implementation
===================

Synergistic Program ANalyzer Implementation.

SPAN is a system built as a framework in Python/Cython language with some C++ code to interface with Clang compiler to generate the IR from a C program.
It understands its own custom intermediate representation called SPAN IR. The following system functions can be explicitly controlled,

* The main analysis(es) to perform on the IR. (as a result other analyses can be used as a helper analyses)
* Context Sensitive vs. Context Insensitive. Many custom analysis methods can be added to the framework in a modular way.
* Maximum number of analyses to invoke simultaneously. This is useful to limit the resource utilization like time and memory.
* Disable specific analyses/ information type to control the system execution.
* Disable a category of statment views (to experiment).
* And more...

