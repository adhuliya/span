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
  action = "iipa",  # command line sub-command
  analysesExpr = "/+IntervalA+PointsToA/",
  results = {
    "analysis.results": {
      "IntervalA": {
        "f:main": { # data flow value at given node numbers
          8 : ("has: {'v:main:x': (11,11)}", "any"), # IN/OUT/False/True values
        },
      }, # end analysis IntervalA
    }, # end analysis.results
    "ipa.vc.table.maxsize": 3, # IPA check
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results
