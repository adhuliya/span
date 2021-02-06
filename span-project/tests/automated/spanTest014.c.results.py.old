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
          5: dfv.NodeDfvL( # b = *x
          #4. (b = *x): IN: {x: {'c'}, b: Bot, c: {'a'}}, OUT: {x: {'c'}, b: {'a'}, c: {'a'}}
            dfvIn= pointsto.OverallL(None, val={
              "v:main:x": pointsto.ComponentL(None, val={'v:main:c'}),
              "v:main:b": pointsto.ComponentL(None, bot=True),
              "v:main:c": pointsto.ComponentL(None, val={'v:main:a'}),
              "g:1d": pointsto.ComponentL(None, bot=True),
              # "g:stdin": pointsto.ComponentL(None, bot=True),
              # "g:stdout": pointsto.ComponentL(None, bot=True),
              # "g:stderr": pointsto.ComponentL(None, bot=True),
              # "g:sys_errlist": pointsto.ComponentL(None, bot=True),
            }),
            dfvOut= pointsto.OverallL(None, val={
              "v:main:x": pointsto.ComponentL(None, val={'v:main:c'}),
              "v:main:b": pointsto.ComponentL(None, val={'v:main:a'}),
              "v:main:c": pointsto.ComponentL(None, val={'v:main:a'}),
              "g:1d": pointsto.ComponentL(None, bot=True),
              # "g:stdin": pointsto.ComponentL(None, bot=True),
              # "g:stdout": pointsto.ComponentL(None, bot=True),
              # "g:stderr": pointsto.ComponentL(None, bot=True),
              # "g:sys_errlist": pointsto.ComponentL(None, bot=True),
            }),
          ),
        }
      },

    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

