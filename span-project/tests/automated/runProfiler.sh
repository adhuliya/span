#!/usr/bin/env bash

# install the necessary software
# `sudo -H pip3 install pyprof2calltree`

python3 -m cProfile -o span.profile ../../span.py test all

# opens the KCacheGrind window showing
# cumulative time taken by each function
nohup pyprof2calltree -k -i span.profile &> /dev/null &
