#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021

"""
This is a new concept under development.

This module defines the Value class and its subclasses.
"""

from typing import Optional, List, Dict, Set
import span.ir.types as types


class Value:
  """
  A Value is an abstract entity, that has various
  abstract mathematical/numerical properties
  (like even/odd, zero, +ve, -ve, range etc.).

  These abstract properties are
  collected from various analyses, and put together
  into a single object.
  A Value object would replace the variables and constants
  that occur in the instructions. This will make the IR
  more abstract.
  """


  def __init__(self):
    # the name of the entity this object represents
    self.name: Optional[str] = ""
    # the type of the value
    self.type: types.Type


  pass
