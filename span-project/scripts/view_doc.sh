#!/usr/bin/env bash

# View the documentation of SPAN (live).
# ref: https://pdoc3.github.io/pdoc/
# INSTALL: pip3 install pdoc3

_PDOC_PORT=5065
export PYTHONPATH="." 

if [[ ! -f span/__init__.py ]]; then
  echo "ERROR: Current directory doesnot contain span package";
fi

if command -v pdoc &> /dev/null; then
  pdoc3 --http 0.0.0.0:$_PDOC_PORT span main.py &
  echo "IMPORTANT: Manually kill pdoc server (pdoc3): PID `pgrep pdoc3`";
  sleep 2 # wait for the server to be ready
  nohup firefox http://localhost:${_PDOC_PORT}/span &> /dev/null &
else
  echo "ERROR: Please install pdoc3: 'pip3 install pdoc3'";
fi
