# a python dictionary with desired states in SPAN

# this files exptects necessary imports in the module eval()ing it.

# import span.ir.types as types
# import span.ir.op as op
# import span.ir.expr as expr
# import span.ir.instr as instr
# import span.ir.constructs as constructs
# import span.ir.tunit as tunit
# import span.ir.ir as ir
# import span.tests.testing as testing

# import span.clients.liveness as liveness

# BLOCK START: list of test actions and results
[

TestActionAndResult(
  action = "ianalyze",  # command line sub-command
  analysesExpr = "/+IntervalA+PointsToA/",
  results = {
    "analysis.results": {
      "IntervalA": {
        "f:main": { # data flow value at given node numbers
          6 : ("has: {'v:main:a': (1,1)}",), # IN/OUT/False/True values
        }
      }, # end analysis LiveVarsA
      "PointsToA": {
        "f:main": { # data flow value at given node numbers
          4 : ("any", "has: {'v:main:b': {'v:main:a'}}",), # IN/OUT/False/True values
        }
      }, # end analysis LiveVarsA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

