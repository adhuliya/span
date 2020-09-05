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
  action = "c2spanir", # analyze/diagnose/c2spanir
  analyses = [], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    'ir.cfg.node.count': 5, # the total nodes in the cfg
    'ir.var.count': 1, # the total vars in the translation unit
    'ir.func.count': 1, # total functions (with or without body) 'ir.func.def.count': 1, # total functions with definitions
    'ir.func.dec.count': 0, # total functions with declaration only
    'ir.record.count': 0, # total functions with declaration only
    'ir.tunit': tunit.TranslationUnit(
      name = "spanTest011.c",
      description = "Auto-Translated from Clang AST.",

      globalInits = [],

      allVars = {
        "v:main:1if": types.Int32,
        "v:main:argv": types.Ptr(to=types.Ptr(to=types.Int8)),
        "v:main:argc": types.Int32,
        "v:main:a": types.Int32,
        "v:main:tmp": types.Int32,
        "v:main:u": types.Ptr(to=types.Int32),
        "v:main:b": types.Int32,
      }, # end allVars dict

      allRecords = {
      }, # end allRecords dict
     
      allFunctions = {
      
        "f:main":
          constructs.Func(
            name = "f:main",
            paramNames = ["v:main:argc", "v:main:argv"],
            variadic = False,
            returnType = types.Int32,

            # Note: -1 is always start/entry BB. (REQUIRED)
            # Note: 0 is always end/exit BB (REQUIRED)
            instrSeq = [
                instr.AssignI(expr.VarE("v:main:a", Info(Loc(3,3))), expr.LitE(11, Info(Loc(3,7))), Info(Loc(3,3))),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(4,3))), expr.LitE(13, Info(Loc(4,7))), Info(Loc(4,3))),
                instr.AssignI(expr.VarE("v:main:u", Info(Loc(5,3))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(5,8))), Info(Loc(5,7))), Info(Loc(5,3))),
                instr.LabelI("1WhileCond"),
                instr.AssignI(expr.VarE("v:main:1if", Info(Loc(7,9))), expr.BinaryE(expr.VarE("v:main:argc", Info(Loc(7,9))), op.BO_GT, expr.LitE(0, Info(Loc(7,16))), Info(Loc(7,9))), Info(Loc(7,9))),
                instr.CondI(expr.VarE("v:main:1if", Info(Loc(7,9))), "1WhileBody", "1WhileExit", Info(Loc(7,9))),
                instr.LabelI("1WhileBody"),
                instr.AssignI(expr.VarE("v:main:tmp", Info(Loc(8,5))), expr.DerefE(expr.VarE("v:main:u", Info(Loc(8,12))), Info(Loc(8,11))), Info(Loc(8,5))),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(9,5))), expr.BinaryE(expr.VarE("v:main:tmp", Info(Loc(9,9))), op.BO_MOD, expr.LitE(2, Info(Loc(9,15))), Info(Loc(9,9))), Info(Loc(9,5))),
                instr.CondI(expr.VarE("v:main:b", Info(Loc(10,8))), "2IfTrue", "2IfFalse", Info(Loc(10,8))),
                instr.LabelI("2IfTrue"),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(11,7))), expr.LitE(15, Info(Loc(11,11))), Info(Loc(11,7))),
                instr.GotoI("2IfExit"),
                instr.LabelI("2IfFalse"),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(13,7))), expr.LitE(16, Info(Loc(13,11))), Info(Loc(13,7))),
                instr.LabelI("2IfExit"),
                instr.AssignI(expr.VarE("v:main:u", Info(Loc(15,5))), expr.AddrOfE(expr.VarE("v:main:b", Info(Loc(15,10))), Info(Loc(15,9))), Info(Loc(15,5))),
                instr.AssignI(expr.VarE("v:main:argc", Info(Loc(16,5))), expr.BinaryE(expr.VarE("v:main:argc", Info(Loc(16,5))), op.BO_SUB, expr.LitE(1, Info(Loc(16,13))), Info(Loc(16,5))), Info(Loc(16,5))),
                instr.GotoI("1WhileCond"),
                instr.LabelI("1WhileExit"),
                instr.ReturnI(expr.VarE("v:main:b", Info(Loc(18,10))), Info(Loc(18,3))),
            ], # instrSeq end.
          ), # f:main() end. 

      }, # end allFunctions dict
    ), # tunit.TranslationUnit() ends

    "ir.names.1": ("f:main",
        types.Int32,
        {"v:main:1if", "v:main:argc", "v:main:a", "v:main:tmp", "v:main:b"}),
  }
),

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["PointsToA", "ConstA", "EvenOddA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "EvenOddA": {
        "f:main": {
          14: dfv.NodeDfvL( # return b
            dfvIn= evenodd.OverallL(None, val={
              "v:main:a": evenodd.ComponentL(None, val=False),
              "v:main:b": evenodd.ComponentL(None, val=False),
              "v:main:tmp": evenodd.ComponentL(None, bot=True),
              "v:main:argc": evenodd.ComponentL(None, bot=True),
              # "v:main:1if": evenodd.ComponentL(None, val=True),
              "g:3d": evenodd.ComponentL(None, bot=True),
              "g:4d": evenodd.ComponentL(None, bot=True),
            }),
            dfvOut= evenodd.OverallL(None, val={
              "v:main:a": evenodd.ComponentL(None, val=False),
              "v:main:b": evenodd.ComponentL(None, val=False),
              "v:main:tmp": evenodd.ComponentL(None, bot=True),
              "v:main:argc": evenodd.ComponentL(None, bot=True),
              # "v:main:1if": evenodd.ComponentL(None, val=True),
              "g:3d": evenodd.ComponentL(None, bot=True),
              "g:4d": evenodd.ComponentL(None, bot=True),
            }),
          ),
        }
      }, # end analysis EvenOddA

    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["IntervalA", "PointsToA", "EvenOddA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "IntervalA": {
        "f:main": {
          14: dfv.NodeDfvL( # return b
            dfvIn= interval.OverallL(None, val={
              "v:main:a": interval.ComponentL(None, val=(11,11)),
              "v:main:b": interval.ComponentL(None, val=(13,15)),
            }),
            dfvOut= interval.OverallL(None, val={
              "v:main:a": interval.ComponentL(None, val=(11,11)),
              "v:main:b": interval.ComponentL(None, val=(13,15)),
            }),
          ),
        }
      }, # end analysis IntervalA

      "PointsToA": {
        "f:main": {
          14: dfv.NodeDfvL( # return b
            dfvIn= pointsto.OverallL(None, val={
              "v:main:u": pointsto.ComponentL(None, val={"v:main:a", "v:main:b"}),
              "v:main:argv": pointsto.ComponentL(None, bot=True),
              "g:1d": pointsto.ComponentL(None, bot=True),
              "g:2d": pointsto.ComponentL(None, bot=True),
            }),
            dfvOut= pointsto.OverallL(None, val={
              "v:main:u": pointsto.ComponentL(None, val={"v:main:a", "v:main:b"}),
              "v:main:argv": pointsto.ComponentL(None, bot=True),
              "g:1d": pointsto.ComponentL(None, bot=True),
              "g:2d": pointsto.ComponentL(None, bot=True),
            }),
          ),
        }
      }, # end analysis IntervalA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult
]
# BLOCK END  : list of test actions and results

