#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""Register the diagnosis created.

Import the class that represents the diagnoses.
This makes the diagnosis class visible in this module.
The sys package imports this module and records all the classes that
are subclasses of `span.api.diagnoses.DiagnosisRT` class.
"""

################################################
# BOUND START: import_the_diagnosis_class_here
################################################

# from span.diagnoses.deadstore import DeadStoreR
# from span.diagnoses.constants import ConstantsCountR
from span.diagnoses.arrayindex import ArrayIndexOutOfBoundsR
from span.diagnoses.avgderef import AvgDerefR
from span.diagnoses.divbyzero import DivByZeroR
from span.diagnoses.nullderef import NullDerefR
from span.diagnoses.constants import ConstantsUsedR
from span.diagnoses.unreachable import UnreachableCodeR
from span.diagnoses.uninitvars import UninitializedVarsR

################################################
# BOUND END  : import_the_diagnosis_class_here
################################################
