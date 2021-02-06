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
      name = "spanTest105.c",
      description = "Auto-Translated from Clang AST.",
    
      allVars = {
        "v:main:1t": types.Int32,
        "v:main:n1": types.Struct("s:Node"),
        "v:main:n2": types.Struct("s:Node"),
      }, # end allVars dict
    
      globalInits = [
      ], # end globalInits.
    
      allRecords = {
        "s:Node":
          types.Struct(
            name = "s:Node",
            members = [
              ("val", types.Int32),
              ("next", types.Ptr(to=types.Struct("s:Node"))),
            ],
            info = Info(Loc(1,1)),
          ),
    
      }, # end allRecords dict
    
      allFunctions = {
        "f:main":
          constructs.Func(
            name = "f:main",
            paramNames = [],
            variadic = False,
            returnType = types.Int32,
    
            instrSeq = [
                instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n1", Info(Loc(8,3))), Info(Loc(8,3))), expr.LitE(10, Info(Loc(8,12))), Info(Loc(8,3))),
                instr.AssignI(expr.VarE("v:main:n2", Info(Loc(9,3))), expr.VarE("v:main:n1", Info(Loc(9,8))), Info(Loc(9,3))),
                instr.AssignI(expr.VarE("v:main:1t", Info(Loc(10,10))), expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(10,10))), Info(Loc(10,10))), Info(Loc(10,10))),
                instr.ReturnI(expr.VarE("v:main:1t", Info(Loc(10,10))), Info(Loc(10,3))),
            ], # instrSeq end.
          ), # f:main() end. 
    
      }, # end allFunctions dict
    ) # tunit.TranslationUnit() ends
  } # end TestActionAndResult.results dictionary
),

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["ConstA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "ConstA": {
        "f:main": {
          5 : dfv.NodeDfvL( # (return 1t)
            dfvIn= const.OverallL(None, val={
              "v:main:n1.val": const.ComponentL(None, val=10),
              "v:main:n2.val": const.ComponentL(None, val=10),
              "v:main:1t": const.ComponentL(None, val=10),
            }),

            dfvOut= const.OverallL(None, val={
              "v:main:n1.val": const.ComponentL(None, val=10),
              "v:main:n2.val": const.ComponentL(None, val=10),
              "v:main:1t": const.ComponentL(None, val=10),
            }),
          ),
        }
      }, # end analysis ConstA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results
