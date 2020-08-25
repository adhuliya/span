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
    'ir.tunit':
      tunit.TranslationUnit(
        name = "spanTest016.c",
        description = "Auto-Translated from Clang AST.",
      
        globalInits = [],

        allVars = {
          "v:main:1if": types.Int32,
          "v:main:a": types.Int32,
          "v:main:c": types.Ptr(to=types.Int32),
          "v:main:b": types.Int32,
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
                  instr.AssignI(expr.VarE("v:main:c", Info(Loc(3,3))), expr.LitE(0, Info(Loc(3,7))), Info(Loc(3,3))),
                  instr.AssignI(expr.VarE("v:main:1if", Info(Loc(4,7))), expr.BinaryE(expr.VarE("v:main:c", Info(Loc(4,7))), op.BO_NE, expr.LitE(0, Info(Loc(4,12))), Info(Loc(4,7))), Info(Loc(4,7))),
                  instr.CondI(expr.VarE("v:main:1if", Info(Loc(4,7))), "1IfTrue", "1IfFalse", Info(Loc(4,7))),
                  instr.LabelI("1IfTrue"),
                  instr.AssignI(expr.DerefE(expr.VarE("v:main:c", Info(Loc(5,6))), Info(Loc(5,5))), expr.LitE(10, Info(Loc(5,10))), Info(Loc(5,5))),
                  instr.GotoI("1IfExit"),
                  instr.LabelI("1IfFalse"),
                  instr.LabelI("1IfExit"),
                  instr.ReturnI(expr.VarE("v:main:a", Info(Loc(6,10))), Info(Loc(6,3))),
              ], # instrSeq end.
            ), # f:main() end. 
      
        }, # end allFunctions dict
      ) # tunit.TranslationUnit() ends
  }
),

]
# BLOCK END  : list of test actions and results

