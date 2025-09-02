SPAN IR is a three-address code which is built layer by layer to define the complete IR and its representation.

1. Types - The types of values (strings, numbers, booleans, etc) that make up the data used in a program.
2. Entities - Entities like constants, variables, functions that make up the program.
3. Expression - Binary, unary and simple expressions that make up any computation.
4. Instruction - Expressions become part of instructions that may assign, call or return the expression value.
5. Basic Block - A sequence of instructions make a basic block.
6. Control Flow Graph (CFG) - A graph where each node is a basic block.
7. Function - Its body is a CFG.
8. TU - A translation Unit which contains global variable declaration, initializations and functions.