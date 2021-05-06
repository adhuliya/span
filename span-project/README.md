Synergistic Program ANalysis (SPAN)
===================================
Author: Anshuman Dhuliya

To run the project use the script: `./main.py`

Note: The whole span library is in `span/`.

IMPORTANT: SPAN is dependent on [SLANG](https://github.com/adhuliya/SLANG) for
its IR generation from a C program.

Note: `spanir/` (if present) is an independent copy of the `span.ir` package, and the
necessary modules needed to run it. (see `spanir/copyIr.sh`)


Coding Style
-------------

Using [google's style guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings) with some exceptions.

Exceptions,
1. 2 space indentation.
2. Using "form ... import ..." syntax
3. Few others (TODO: document)

[PEP8](https://www.python.org/dev/peps/pep-0008/) is also a useful read.

Project Structure
---------------

The project structure is inspired from [realpython.com](https://realpython.com/python-application-layouts/).


License
--------

This project uses MIT license as taken from [chooselicense.com](https://choosealicense.com/licenses/mit/)


FAQs
------

### How to run?
Use the `main.py` script to run the project.
Run `./main.py help` to see the command line usage.


### How to add a new analysis?
All analyses are implemented in the package `span.clients` in their own modules.
Take a look at the following analyses to get more detailed idea
(since not all information can be provided here within this document's scope),
* `span.clients.const` (`span/clients/const.py`)
* `span.clients.liveness`
* `span.clients.pointsto`
* `span.clients.evenodd`

Every analysis has to be registered in the module
`span.clients.register`.
For example, Points-to analysis is registered as,

    from span.clients.pointsto import PointsToA
    
Here `PointsToA` is the class that implements the Points-to analysis.

An analysis specification makes use of the analysis API reference from `span.api`
and IR API reference from `span.ir` package and their sub-modules.


### What goes inside an analysis?
* Take a look at `span.clients.const` and `span.clients.liveness`
  to get the complete idea of an analysis implementation.
* Every analysis subclasses `span.api.analysis.AnalysisAT` class.
* Every analysis has the following class variables,
   * L (Lattice):   a subclass of `span.api.lattice.DataLT`
   * D (Direction): ForwardD, BackwardD, or a custom ForwBackD direction class.
   * SimNeed (Simplification Need): A list identifying the blocking expressions.
* Every analysis overrides the following,
   * Instruction transfer functions, for e.g.
      * `Num_Assign_Var_Var_Instr   (InstrIT, NodeDfv) -> NodeDfv`
      * `Num_Assign_Var_Lit_Instr   (InstrIT, NodeDfv) -> NodeDfv`
      * `Ptr_Assign_Deref_Var_Instr (InstrIT, NodeDfv) -> NodeDfv`
      * `Num_Assign_Var_Call_Instr  (InstrIT, NodeDfv) -> NodeDfv`
      
     Look at `span.api.analysis.AnalysisT` class
     for all the available transfer functions and their documentation.
      
   * The simplifications it can do, which are,
      * `Node__to__Nil       (node, nodeDfv)         -> sim.SimToNilL`
      * `LhsVar__to__Nil     (expr.VarE, NodeDfv)    -> sim.SimToLiveL`
      * `Deref__to__Vars     (expr.UnaryE, NodeDfv)  -> sim.SimToVarsL`
      * `Num_Bin__to__Num_Lit(expr.BinaryE, NodeDfv) -> sim.SimToValL`
      * `Num_Var__to__Num_Lit(expr.VarE, NodeDfv)    -> sim.SimToValL`
      * `Cond__to__UnCond    (expr.VarE, NodeDfv)    -> sim.SimToBoolL`
      
      Look at `span.api.sim` module for complete simplification information.

### What do suffixes like `T`, `A`, `AT`, `DT`, `LT` mean in class names?
Suffixes have been added to immediately distinguish a name from the crowd.

* `T` suffix means its completely an abstract type
   (made for the sake of logical hierarchy) not to be instantiated.
   If present it is always the last character of the name.
   This suffix can be used with the others below.
* `A` suffix means the class is an analysis.
* `I` suffix means the class is an instruction.
* `E` suffix means the class is an expression.
* `O` suffix means the class is an operator.
* `D` suffix means the class is a direction.
* `L` suffix means the class is a lattice.
* `R` suffic means the class is a bug reporting class.
* `DT` suffix means the class is a direction and is abstract.
* `ET` suffix means the class is an expression and is abstract.
* `...`

### How are lattices implemented?
All lattices in the system except `lattice.ChangeL` are subclasses
of `lattice.LatticeLT` class. Lattice of an analysis should subclass
`lattice.DataLT`. The following points are important,
* All `DataLT` lattices are bound to a function.
* Take a look at lattice classes, `span.clients.const.ConstL`
  and `span.clients.liveness.LiveL`.
* **All lattice objects should be immutable** (i.e. always create
  a copy and change the copy's contents)
  -- this is critical for correctness.
* If a lattice object is Top or Bot, then specifically mark it as such. For example,
   * `const.ConstL(function, top=True)`
   * `const.ConstL(function, bot=True)`
  
  Note that the `function` argument is necessary
  to instantiate an instance of a lattice.
   
  The system relies on the explicit Top and Bot flags.
  For example, it can create Top and Bot values for any
  analysis on the fly using the above given constructors.
  
  Analysis's lattice is its internal representation.
  Span doesn't care about the internal data structures
  used by the analysis. Span is only interested in the
  interface an analysis must provide.
* The following interfaces expose the lattice to SPAN,
   * `meet(other: LatticeLT) -> Tuple[LatticeLT, ChangeL]`
   * `__lt__(other: LatticeLT) -> bool`
   
     It implements the weaker-than relation (not strictly-weaker-than).
     * if `x > y or x < y` is False, then `x` and `y` are incomparable.
     * if `x > y and x < y` is True, then `x` and `y` are equal.
    
   * `__eq__(other: LatticeLT) -> bool` equality relation
   
### How to debug/ assist your development?
SPAN has an elaborate logging mechanism. The following log file is generated by default,

    ~/.itsoflife/local/logs/span-logs/span.log
    
A rotating logger is used so look out for other log files in the same directory.
You can change the logging level by editing the following line
in `main.py`,

    logger.initLogger(appName="span", logLevel=logger.LogLevels.DEBUG)

#### System wide switches
Span uses system wide switches to enable or disable some features.
See the module `span.util.util` for their documentation.
The most important switch among them is,
* LS (Logger Switch)


LS is used to control logging. Although, loggers have their own
levels to control logging, using this switch has shown to
speed up production code by almost 30%. The recommended usage is,


    from span.util.util import LS
    ...
    if LS: _log.debug("your msg: %s, %s", param1, param2)
    
### How to type check the code?

Install `mypy` and cd to the directory that contains the `span` package,
and run the following command,

    mypy span |& tee mypy.out;
    
### How to profile your code?
To monitor the efficiency of the implementation, its necessary
to profile your code now and then. Do the following to profile the code,

Install the necessary software,

    sudo -H pip3 install pyprof2calltree

Use it as follows,

    python3 -m cProfile -o span.profile ./main.py
    pyprof2calltree -k -i span.profile

A KCacheGrind window will appear with cumulative time taken in each function.
See [this resource](https://julien.danjou.info/guide-to-python-profiling-cprofile-concrete-case-carbonara/) for more information.


## Clang Bug Reporter

Using scan-build for DeadStores:

    scan-build -enable-checker deadcode.DeadStores -V clang -c -std=c99 spanTest011.c 
    
Using span:

    span diagnose DeadStoreR span spanTest011.c
    
See the list of checkers available:

    clang -cc1 -analyzer-checker-help-developer | less    


## Transformations Possible
1. `if` statement simplification (`&& 0`, `|| 1`)
2. Dead code elimination (`x = ...` to NopI)
3. Relational expressions to `0` or `1`
4. Pointer based function call to direct function call.
5. Use Reaching Definitions to replace a variable with another.


## TODOs
1. Collect many possible benchmark programs. (done: see `tests/benchmarks/finalized/` folder)
   * TODO: prepare some programs in the coreutils for analysis.
2. Merge C files of the collected benchmark programs.
   * TODO: for coreutils.
3. Add necessary computation comparisons in SPAN:
   * Array index check.
   * Divide by zero check.
4. Generate results on 5 of the benchmarks.
5. Remove all unsafe `is` tests (to handle cython's limitations). (DONE - TODO: recheck)
6. Remove sim of ptr-array-subscript expressions in cascading and lerner's.
7. Handle initializer expressions a[] = {{1,2},{3,4}};
8. Add cascading to IPA.
9. Test cascading in IPA mode -- +add test cases.
10. Add test case for the NULL pointee in the pointee set (DONE).
11. Treat appropriate pointer arithmetic as ptr-array-subscript operations.


1. List of (library) functions that don't result in over-approximation.
4. Transformation improvement.


## Notes

### C99 Incompatibilities
* Varargs not supported. (okay - tolerable)
* Aggregate assignment not supported. E.g. arr[] = {1,2,3}. (support it)
* size_t is assumed UINT64. (okay - tolerable)
* All floats are considered FLOAT64. (okay - tolerable)
* static initializations in functions? (Supported) (DONE)

### SPAN Features
* Flow Insensitive (Easy to add. Maybe not efficient.)
* Intra-Procedural (SPAN, Cascade, Lerner's)
* Inter-Procedural (SPAN, Cascade, Lerner's)
* Demand Driven Method (#DDM) (Intra) (Akshat)
* Query Interface.
* Test Framework.
* Forward & Backward Support (TODO: Test BiDirectional)



<br /> <br /> <br />
&copy; 2020 Anshuman Dhuliya
<br /> <br /> <br />

