#!/usr/bin/env bash

# Reference:
#   http://www.blog.pythonlibrary.org/2016/07/20/an-intro-to-coverage-py/
#   https://coverage.readthedocs.io/en/latest/config.html#syntax

# install coverage: `sudo pip3 install coverage`

# make sure `.coveragerc` files has desired settings
# run coverage: it generates `.coverage` file
coverage run ../../main.py test all

# generate html report from `.coverage` file
# this genrates `htmlcov/` folder
coverage html

nohup firefox htmlcov/index.html &> /dev/null &
