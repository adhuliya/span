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
    'ir.func.count': 1, # total functions (with or without body)
    'ir.func.def.count': 1, # total functions with definitions
    'ir.func.dec.count': 0, # total functions with definitions

    'ir.tunit' : tunit.TranslationUnit(
       name = "spanTest050.c",
       description = "Auto-Translated from Clang AST.",
     
       globalInits = [],
    
       allVars = {
         "v:main:v": types.Ptr(to=types.Int32),
         "v:main:arr": types.ConstSizeArray(of=types.Int32, size=10),
         "v:main:u": types.Ptr(to=types.Int32),
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
               instr.AssignI(expr.VarE("v:main:u", Info(Loc(6,3))), expr.VarE("v:main:arr", Info(Loc(6,7))), Info(Loc(6,3))),
               instr.AssignI(expr.VarE("v:main:v", Info(Loc(7,3))), expr.AddrOfE(expr.VarE("v:main:arr", Info(Loc(7,8))), Info(Loc(7,7))), Info(Loc(7,3))),
               instr.ReturnI(expr.LitE(0, Info(Loc(8,10))), Info(Loc(8,3))),
             ], # instrSeq end.
           ), # f:main() end. 
     
       }, # end allFunctions dict
    ), # tunit.TranslationUnit() ends

    "ir.names.1": ("global",
      None,
      {"g:0Null", "v:main:arr"}),

    "ir.names.2": ("f:main",
      types.Ptr(to=types.Int32),
      {"v:main:v", "v:main:u"})

  } # end results
), # end TestActionAndResult

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["PointsToA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "PointsToA": {
        "f:main": {
          2 : dfv.NodeDfvL( # (u = arr)
            dfvIn= pointsto.OverallL(None, bot=True),
            dfvOut= pointsto.OverallL(None, val={
              "v:main:u": pointsto.ComponentL(None, val={'v:main:arr'}),
              "v:main:v": pointsto.ComponentL(None, bot=True),
            }),
          ),

          3 : dfv.NodeDfvL( # (v = &arr)
            dfvIn= pointsto.OverallL(None, val={
              "v:main:u": pointsto.ComponentL(None, val={'v:main:arr'}),
              "v:main:v": pointsto.ComponentL(None, bot=True),
            }),
            dfvOut= pointsto.OverallL(None, val={
              "v:main:u": pointsto.ComponentL(None, val={'v:main:arr'}),
              "v:main:v": pointsto.ComponentL(None, val={'v:main:arr'}),
            }),
          ),

          5 : dfv.NodeDfvL( # nop()
            dfvIn= pointsto.OverallL(None, val={
              "v:main:u": pointsto.ComponentL(None, val={'v:main:arr'}),
              "v:main:v": pointsto.ComponentL(None, val={'v:main:arr'}),
            }),
            dfvOut= pointsto.OverallL(None, val={
              "v:main:u": pointsto.ComponentL(None, val={'v:main:arr'}),
              "v:main:v": pointsto.ComponentL(None, val={'v:main:arr'}),
            }),
          ),
        }
      }, # end analysis PointsToA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]

