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
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["ConstA", "StrongLiveVarsA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "ConstA": {
        "f:main": {
          2 : dfv.NodeDfvL( # (a=5)
            dfvIn= const.OverallL(None, bot=True),
            dfvOut= const.OverallL(None, val={
              "v:main:a": const.ComponentL(None, val=5),
            }),
          ),
        }
      }, # end analysis ConstA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

