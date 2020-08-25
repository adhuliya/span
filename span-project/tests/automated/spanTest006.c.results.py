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

# import span.clients.pointsto as pointsto
# import span.clients.const as const

# BLOCK START: list of test actions and results
[

TestActionAndResult(
  action = "c2spanir", # analyze/diagnose/c2spanir
  analyses = [], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    'ir.cfg.node.count': 5, # the total nodes in the cfg
    'ir.var.count': 1, # the total vars in the translation unit
    'ir.func.count': 1, # total functions (with or without body)
    'ir.func.def.count': 1, # total functions with definitions
    'ir.func.dec.count': 0, # total functions with declaration only
    'ir.record.count': 0, # total functions with declaration only
    'ir.tunit': tunit.TranslationUnit(
      name = "spanTest006.c",
      description = "Auto-Translated from Clang AST.",

      globalInits = [],

      allVars = {
        "v:main:b": types.Int32,
        "v:main:p": types.Ptr(to=types.Int32),
        "v:main:c": types.Int32,
        "v:main:argc": types.Int32,
        "v:main:a": types.Int32,
      }, # end allVars dict

      allRecords = {
      }, # end allRecords dict
     
      allFunctions = {
      
        "f:main":
          constructs.Func(
            name = "f:main",
            paramNames = ["v:main:argc"],
            variadic = False,
            returnType = types.Int32,

            # Note: -1 is always start/entry BB. (REQUIRED)
            # Note: 0 is always end/exit BB (REQUIRED)
            instrSeq = [
                instr.AssignI(expr.VarE("v:main:a", Info(Loc(5,3))), expr.LitE(10, Info(Loc(5,7))), Info(Loc(5,3))),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(6,3))), expr.LitE(20, Info(Loc(6,7))), Info(Loc(6,3))),
                instr.CondI(expr.VarE("v:main:a", Info(Loc(8,7))), "1IfTrue", "1IfFalse", Info(Loc(8,7))),
                instr.LabelI("1IfTrue"),
                instr.AssignI(expr.VarE("v:main:p", Info(Loc(9,5))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(9,10))), Info(Loc(9,9))), Info(Loc(9,5))),
                instr.GotoI("1IfExit"),
                instr.LabelI("1IfFalse"),
                instr.AssignI(expr.VarE("v:main:p", Info(Loc(11,5))), expr.AddrOfE(expr.VarE("v:main:b", Info(Loc(11,10))), Info(Loc(11,9))), Info(Loc(11,5))),
                instr.LabelI("1IfExit"),
                instr.AssignI(expr.VarE("v:main:c", Info(Loc(14,3))), expr.DerefE(expr.VarE("v:main:p", Info(Loc(14,8))), Info(Loc(14,7))), Info(Loc(14,3))),
                instr.ReturnI(expr.VarE("v:main:c", Info(Loc(15,10))), Info(Loc(15,3))),
            ], # instrSeq end.
          ), # f:main() end. 

      }, # end allFunctions dict
    ) # tunit.TranslationUnit() ends
  }
),

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["PointsToA", "ConstA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "PointsToA": {
        "f:main": {
          7 : dfv.NodeDfvL( # (c = *p)
            dfvIn= pointsto.OverallL(None, val={
              "v:main:p": pointsto.ComponentL(None, {"v:main:a"})
            }),
            dfvOut= pointsto.OverallL(None, val={
              "v:main:p": pointsto.ComponentL(None, {"v:main:a"})
            })
          ),
        }
      }, # end analysis PointsToA

      "ConstA": {
        "f:main": {
          7 : dfv.NodeDfvL( # (c = *p)
            dfvIn= const.OverallL(None, val={
              "v:main:a": const.ComponentL(None, val=10),
              "v:main:b": const.ComponentL(None, val=20),
              "v:main:c": const.ComponentL(None, bot=True),
              "v:main:argc": const.ComponentL(None, bot=True),
            }),

            dfvOut= const.OverallL(None, val={
              "v:main:a": const.ComponentL(None, val=10),
              "v:main:b": const.ComponentL(None, val=20),
              "v:main:c": const.ComponentL(None, val=10),
              "v:main:argc": const.ComponentL(None, bot=True),
            }),
          ),
        }
      }, # end analysis ConstA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["EvenOddA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "EvenOddA": {
        "f:main": {
          6 : dfv.NodeDfvL( # (c = *p)
            dfvIn= evenodd.OverallL(None, val={
              "v:main:a": evenodd.ComponentL(None, val=True),
              "v:main:b": evenodd.ComponentL(None, val=True),
              "v:main:c": evenodd.ComponentL(None, bot=True),
              "v:main:argc": evenodd.ComponentL(None, bot=True),
            }),

            dfvOut= evenodd.OverallL(None, val={
              "v:main:a": evenodd.ComponentL(None, val=True),
              "v:main:b": evenodd.ComponentL(None, val=True),
              "v:main:c": evenodd.ComponentL(None, bot=True),
              "v:main:argc": evenodd.ComponentL(None, bot=True),
            }),
          ),
        }
      }, # end analysis EvenOddA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

