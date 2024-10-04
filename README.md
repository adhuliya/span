SPAN Implementation
===================

Synergistic Program ANalysis Implementation.

SPAN is a system built as a framework in Python/Cython language with some C++. It understands its own custom intermediate representation called The SPAN IR. The following system functions can be explicitly controlled,

* The main analysis to perform on the IR. (as a result all other analyses used are helper analyses)
* Context Sensitive vs. Context Insensitive
* Maximum number of analyses to invoke simultaneously
* Disable specific analyses/ information type.
* Disable a category of expression simplification.

