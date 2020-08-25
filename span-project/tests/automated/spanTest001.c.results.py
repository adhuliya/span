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
      name = "spanTest001.c",
      description = "Auto-Translated from Clang AST.",

      globalInits = [],
    
      allVars = {
        "v:main:x": types.Int32,
      }, # end allVars dict

      allRecords = {
      }, # end allRecords dict
    
      allFunctions = {
    
        "f:main":
          constructs.Func(
            name = "f:main",
            paramNames = [],
            variadic = False,
            returnType = types.Int32,
    
            # Note: -1 is always start/entry BB. (REQUIRED)
            # Note: 0 is always end/exit BB (REQUIRED)
            instrSeq = [
                instr.AssignI(expr.VarE("v:main:x", Info(Loc(3,3))), expr.LitE(20, Info(Loc(3,7))), Info(Loc(3,3))),
                instr.ReturnI(expr.VarE("v:main:x", Info(Loc(4,10))), Info(Loc(4,3))),
            ], # instrSeq end.
          ), # f:main() end. 
    
      }, # end allFunctions dict
    ), # tunit.TranslationUnit() ends
    'ir.names.1': ("global", # i.e. ALL variables
      types.Int32,
      set()),
    'ir.names.2': ("f:main", # i.e. ALL function variables
      types.Int32,
      {"v:main:x"}),
  }
),

# TestActionAndResult(
#   action = "analyze", # analyze/diagnose/c2spanir
#   analyses = ["LiveVarsA"], # which analyses to run
#   diagnoses = [], # diagnoses to run (must initialize)
#   results = {
#     "analysis.results": {
#       "LiveVarsA": {
#         "f:main": {
#           1 : dfv.NodeDfvL( # (return x)
#             dfvIn= liveness.OverallL(None, val={
#               "g:0.Null", "g:dummy/DMY",
#             }),
#             dfvOut= liveness.OverallL(None, bot=True) # all vars live
#           ),
#           2 : dfv.NodeDfvL( # (return x)
#             dfvIn= liveness.OverallL(None, bot=True), # all vars live
#             dfvOut= liveness.OverallL(None, val={
#               "g:0.Null", "g:dummy/DMY",
#             })
#           ),
#         }
#       }, # end analysis LiveVarsA
#     }, # end analysis.results
#   } # end of results
# ), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

