# Synergistic Program Analyzer (SPAN)
A program analysis engine and bug finder tool with its foundation in Abstract Interpretation and Data Flow Analysis.

## The platform

SPAN is a program analysis engine written in Go programming language.
It uses the Clang/LLVM infrastructure to convert a C program to Clang AST
and then to a three-address code intermediate represenation called SPIR (SPAN IR).

## What is SPAN IR (SPIR)?

SPIR is an simple three-address code intermediate representation (IR) which
is built to experiment with different program analysis abstractions and alogirthms.
The goal of SPIR is to provide an IR that lends itself efficiently
to program analysis, and to allow experimentation with different program
analysis algorithms and techniques.

## How is a C program converted to SPIR?

SPAN uses the Clang/LLVM based tool `slang` which converts an input C program
into a Clang AST, which is then visited and serialized to SPIR
using the specification in `spir.proto` protobuf file.
The output of `slang` is a binary/text protobuf message that becomes an input
to `span` program analyzer.

## How are C programs analyzed across files?

A single C file is converted to a single SPIR Translation Unit (SPIR TU or just TU).
SPAN supports a rudimentary static linker which can combine two or more TUs into one.
One can also use Clang's cross translation unit feature to create a single AST for the entire
project and convert that into a single SPIR TU (TODO).

## How to setup Docker container?

Please run `scripts/setup_docker.sh` to setup docker container.
In case of any errors please refer a more detailed README in `docker/README.md`,
or file a bug.


## What are the project design guidelines followed in SPAN?

SPAN is a modular project where each component is developed like a library which can be reused.
Our goal is to define simple components and compose them to achieve the functionality.
We extensively use the interface programming style as encouraged by the Go community.
Wherever possible, SPAN uses standard Go programming practices and SOLID programming
principles to develop a bug free and maintainable project.
You will find all implementation details hidden behind carefully created interfaces.

We welcome and encourage any suggestions for improvments.
It doesn't matter how small or big the suggestions are.
We will be more than happy to hear from you! :)

