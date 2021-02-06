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

# BLOCK START: list of test actions and results
[

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["PointsToA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "PointsToA": {
        "f:main": {
          12: dfv.NodeDfvL( # (*w = 3t)
          # 11. (*w = 3t): IN: OverallL {x: {'a', 'e'}, w: {'y'}, y: {'e', 'b'}, z: {'x', 'y'}}, OUT: OverallL {x: {'a', 'e'}, w: {'y'}, y: {'e'}, z: {'x', 'y'}}
            dfvIn= pointsto.OverallL(None, val={
              "v:main:w": pointsto.ComponentL(None, val={'v:main:y'}),
              "v:main:z": pointsto.ComponentL(None, val={'v:main:y', 'v:main:x'}),
              "v:main:x": pointsto.ComponentL(None, val={'v:main:a', 'v:main:e'}),
              "v:main:y": pointsto.ComponentL(None, val={'v:main:b', 'v:main:e'}),
              "v:main:2t": pointsto.ComponentL(None, val={'v:main:e'}),
              "v:main:3t": pointsto.ComponentL(None, val={'v:main:e'}),
            }),
            dfvOut= pointsto.OverallL(None, val={
              "v:main:w": pointsto.ComponentL(None, val={'v:main:y'}),
              "v:main:z": pointsto.ComponentL(None, val={'v:main:y', 'v:main:x'}),
              "v:main:x": pointsto.ComponentL(None, val={'v:main:a', 'v:main:e'}),
              "v:main:y": pointsto.ComponentL(None, val={'v:main:e'}),
              "v:main:2t": pointsto.ComponentL(None, val={'v:main:e'}),
              "v:main:3t": pointsto.ComponentL(None, val={'v:main:e'}),
            }),
          ),
        }
      },

    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

