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
      name = "spanTest007.c",
      description = "Auto-Translated from Clang AST.",

      globalInits = [],

      allVars = {
        "v:main:y": types.Int32,
        "v:main:argc": types.Int32,
        "v:main:b": types.Int32,
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
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(3,3))), expr.LitE(0, Info(Loc(3,7))), Info(Loc(3,3))),
                instr.CondI(expr.VarE("v:main:b", Info(Loc(4,7))), "1IfTrue", "1IfFalse", Info(Loc(4,7))),
                instr.LabelI("1IfTrue"),
                instr.AssignI(expr.VarE("v:main:y", Info(Loc(5,5))), expr.BinaryE(expr.VarE("v:main:argc", Info(Loc(5,9))), op.BO_ADD, expr.LitE(2, Info(Loc(5,16))), Info(Loc(5,9))), Info(Loc(5,5))),
                instr.GotoI("1IfExit"),
                instr.LabelI("1IfFalse"),
                instr.AssignI(expr.VarE("v:main:y", Info(Loc(7,5))), expr.LitE(20, Info(Loc(7,9))), Info(Loc(7,5))),
                instr.LabelI("1IfExit"),
                instr.ReturnI(expr.VarE("v:main:y", Info(Loc(9,10))), Info(Loc(9,3))),
            ], # instrSeq end.
          ), # f:main() end. 

      }, # end allFunctions dict
    ), # tunit.TranslationUnit() ends
    'ir.names.1': ("global", # i.e. ALL variables
      types.Int32,
      set()),
    'ir.names.2': ("f:main", # i.e. ALL function variables
      types.Int32,
      {"v:main:b", "v:main:y", "v:main:argc"}),
  }
),

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["StrongLiveVarsA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "StrongLiveVarsA": {
        "f:main": {
          3 : dfv.NodeDfvL( # (if (b))
            dfvIn= liveness.OverallL(None, val={
              "v:main:argc", "g:00", "g:0d", "v:main:b", 
            }),
            dfvOut= liveness.OverallL(None, val={
              "v:main:argc", "g:00", "g:0d",
            }),
          ),
        }
      }, # end analysis StrongLiveVarsA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["StrongLiveVarsA", "ConstA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "StrongLiveVarsA": {
        "f:main": {
          3 : dfv.NodeDfvL( # (return x)
            dfvIn= liveness.OverallL(None, val={
              "v:main:b", "g:00", "g:0d",
            }),
            dfvOut= liveness.OverallL(None, val={
              "g:00", "g:0d",
            }),
          ),
        }
      }, # end analysis StrongLiveVarsA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

