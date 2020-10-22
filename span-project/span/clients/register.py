#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Register the analysis written."""

# Import the class that represents the analysis.
# This makes the analysis class visible in this module.
# The host imports this module and records all the classes that
# are subclasses of span.sys.analysis.AnalysisAT class.

################################################
# BOUND START: import_the_analysis_class_here
################################################

from span.clients.const import ConstA
from span.clients.evenodd import EvenOddA
from span.clients.pointsto import PointsToA
from span.clients.interval import IntervalA
from span.clients.stronglive import StrongLiveVarsA
from span.clients.reachingdef import ReachingDefA
# from span.clients.simplelive import LiveVarsA
# from span.clients.reach      import ReachA
# from span.clients.range      import RangeA

################################################
# BOUND END  : import_the_analysis_class_here
################################################
