
# START: A_SPAN_translation_unit!

# eval() the contents of this file.
# Keep the following imports in effect when calling eval.

# import span.ir.types as types
# import span.ir.op as op
# import span.ir.expr as expr
# import span.ir.instr as instr
# import span.ir.constructs as constructs
# import span.ir.tunit as tunit
# from span.ir.types import Loc

# An instance of span.ir.tunit.TranslationUnit class.
tunit.TranslationUnit(
  name = "spanTest008.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:a": types.Int32,
  }, # end allVars dict

  globalInits = [
  ], # end globalInits.

  allRecords = {
  }, # end allRecords dict

  allFunctions = {
    "f:main":
      constructs.Func(
        name = "f:main",
        paramNames = [],
        variadic = False,
        returnType = types.Int32,

        instrSeq = [
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(3,3))), expr.LitE(5, Info(Loc(3,7))), Info(Loc(3,3))),
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(4,3))), expr.BinaryE(expr.VarE("v:main:a", Info(Loc(4,7))), op.BO_ADD, expr.LitE(1, Info(Loc(4,11))), Info(Loc(4,7))), Info(Loc(4,3))),
            instr.ReturnI(expr.VarE("v:main:a", Info(Loc(5,10))), Info(Loc(5,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
