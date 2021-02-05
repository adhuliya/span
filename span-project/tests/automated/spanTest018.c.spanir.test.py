
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
  name = "spanTest018.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:b": types.Int32,
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
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(4,3))), expr.LitE(0, Info(Loc(4,7))), Info(Loc(4,3))),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(5,3))), expr.LitE(0, Info(Loc(5,7))), Info(Loc(5,3))),
            instr.CondI(expr.VarE("v:main:a", Info(Loc(6,6))), "1IfTrue", "1IfFalse", Info(Loc(6,3))),
            instr.LabelI("1IfTrue"),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(7,5))), expr.LitE(20, Info(Loc(7,9))), Info(Loc(7,5))),
            instr.GotoI("1IfExit"),
            instr.LabelI("1IfFalse"),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(9,5))), expr.LitE(10, Info(Loc(9,9))), Info(Loc(9,5))),
            instr.LabelI("1IfExit"),
            instr.ReturnI(expr.VarE("v:main:b", Info(Loc(10,10))), Info(Loc(10,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
