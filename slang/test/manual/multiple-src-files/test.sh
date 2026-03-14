#!/bin/bash

# The proto files are generated next to the source files in their respective locations.
../../../built/rel/slang -p compile_commands.json foo.c bar.c zar/zar.c -bit-spir;