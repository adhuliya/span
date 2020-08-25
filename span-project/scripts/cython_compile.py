#!/usr/bin/env python3

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
  # Extension("span.sys.host",  ["span/sys/host.py"]),
  # Extension("span.sys.diagnosis",  ["span/sys/diagnosis.py"]),
  # Extension("span.sys.clients",  ["span/sys/clients.py"]),
  Extension("span.sys.ddm",  ["span/sys/ddm.py"]),
  #   ... all your modules that need be compiled ...
]

for e in ext_modules:
  e.cython_directives = {'language_level': "3"} #all are Python-3

setup(
  name = 'span_cython',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)

