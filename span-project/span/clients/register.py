#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""Register the user analysis.

Import the analysis class here that subclasses `span.api.analysis.AnalysisAT`.
This makes the analysis class visible in this module.
The host imports this module and registers all the classes that
are subclasses of `span.api.analysis.AnalysisAT` class.
"""

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
# from span.clients.reach      import ReachA  # dead statements

################################################
# BOUND END  : import_the_analysis_class_here
################################################
