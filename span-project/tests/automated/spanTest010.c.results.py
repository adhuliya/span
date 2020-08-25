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
      name = "spanTest010.c",
      description = "Auto-Translated from Clang AST.",

      globalInits = [],

      allVars = {
        "v:main:1if": types.Int32,
        "g:cond": types.Int32,
        "v:main:b": types.Int32,
        "v:main:tmp": types.Int32,
        "v:main:a": types.Int32,
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
                instr.AssignI(expr.VarE("v:main:a", Info(Loc(4,3))), expr.LitE(11, Info(Loc(4,7))), Info(Loc(4,3))),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(5,3))), expr.LitE(13, Info(Loc(5,7))), Info(Loc(5,3))),
                instr.AssignI(expr.VarE("g:cond", Info(Loc(6,3))), expr.LitE(10, Info(Loc(6,10))), Info(Loc(6,3))),
                instr.AssignI(expr.VarE("v:main:u", Info(Loc(7,3))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(7,8))), Info(Loc(7,7))), Info(Loc(7,3))),
                instr.LabelI("1WhileCond"),
                instr.AssignI(expr.VarE("v:main:1if", Info(Loc(9,9))), expr.BinaryE(expr.VarE("g:cond", Info(Loc(9,9))), op.BO_GT, expr.LitE(1, Info(Loc(9,16))), Info(Loc(9,9))), Info(Loc(9,9))),
                instr.CondI(expr.VarE("v:main:1if", Info(Loc(9,9))), "1WhileBody", "1WhileExit", Info(Loc(9,9))),
                instr.LabelI("1WhileBody"),
                instr.AssignI(expr.VarE("v:main:tmp", Info(Loc(10,5))), expr.DerefE(expr.VarE("v:main:u", Info(Loc(10,12))), Info(Loc(10,11))), Info(Loc(10,5))),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(11,5))), expr.BinaryE(expr.VarE("v:main:tmp", Info(Loc(11,9))), op.BO_MOD, expr.LitE(2, Info(Loc(11,15))), Info(Loc(11,9))), Info(Loc(11,5))),
                instr.CondI(expr.VarE("v:main:b", Info(Loc(12,8))), "2IfTrue", "2IfFalse", Info(Loc(12,8))),
                instr.LabelI("2IfTrue"),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(13,7))), expr.LitE(15, Info(Loc(13,11))), Info(Loc(13,7))),
                instr.GotoI("2IfExit"),
                instr.LabelI("2IfFalse"),
                instr.AssignI(expr.VarE("v:main:b", Info(Loc(15,7))), expr.LitE(16, Info(Loc(15,11))), Info(Loc(15,7))),
                instr.LabelI("2IfExit"),
                instr.AssignI(expr.VarE("v:main:u", Info(Loc(17,5))), expr.AddrOfE(expr.VarE("v:main:b", Info(Loc(17,10))), Info(Loc(17,9))), Info(Loc(17,5))),
                instr.AssignI(expr.VarE("g:cond", Info(Loc(18,5))), expr.BinaryE(expr.VarE("g:cond", Info(Loc(18,5))), op.BO_ADD, expr.LitE(1, Info(Loc(18,13))), Info(Loc(18,5))), Info(Loc(18,5))),
                instr.GotoI("1WhileCond"),
                instr.LabelI("1WhileExit"),
                instr.ReturnI(expr.VarE("v:main:b", Info(Loc(20,10))), Info(Loc(20,3))),
            ], # instrSeq end.
          ), # f:main() end. 

      }, # end allFunctions dict
    ) # tunit.TranslationUnit() ends
  }
),

TestActionAndResult(
  action = "analyze", # analyze/diagnose/c2spanir
  analyses = ["ConstA", "EvenOddA", "PointsToA"], # which analyses to run
  diagnoses = [], # diagnoses to run (must initialize)
  results = {
    "analysis.results": {
      "EvenOddA": {
        "f:main": {
          11 : dfv.NodeDfvL( # (b = 16)
            dfvIn  = evenodd.OverallL(None, top=True),
            dfvOut = evenodd.OverallL(None, top=True),
          ),
        }
      }, # end analysis EvenOddA

    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

