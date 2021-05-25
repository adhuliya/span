#!/usr/bin/env bash

# View the documentation of SPAN (live).
# ref: https://pdoc3.github.io/pdoc/
# INSTALL: pip3 install pdoc3

_PDOC_PORT=5065
_PID_FILE="pdoc3.pid"
export PYTHONPATH="."

if [[ ! -f span/__init__.py ]]; then
  echo "ERROR: Current directory doesnot contain span package";
fi

if command -v pdoc3 &> /dev/null; then
  pdoc3 --http 0.0.0.0:$_PDOC_PORT span main.py &
  echo "IMPORTANT: Manually kill pdoc server (pdoc3): PID `pgrep pdoc3`";
  pgrep pdoc3 > $_PID_FILE;
  echo "NOTE: Written process id of pdoc3 server in ./$_PID_FILE";
  sleep 3; # wait for the server to be ready
  nohup firefox http://localhost:${_PDOC_PORT}/span &> /dev/null &
else
  echo "ERROR: Please install pdoc3: 'pip3 install pdoc3'";
fi
