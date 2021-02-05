
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
  name = "spanTest021.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:p": types.Ptr(to=types.Int32),
    "v:main:a": types.Int32,
    "v:main:b": types.Int32,
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
            instr.AssignI(expr.VarE("v:main:p", Info(Loc(8,3))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(8,13))), Info(Loc(8,12))), Info(Loc(8,3))),
            instr.LabelI("1WhileCond"),
            instr.CondI(expr.VarE("v:main:a", Info(Loc(9,9))), "1WhileBody", "1WhileExit", Info(Loc(9,9))),
            instr.LabelI("1WhileBody"),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(10,5))), expr.DerefE(expr.VarE("v:main:p", Info(Loc(10,10))), Info(Loc(10,9))), Info(Loc(10,5))),
            instr.CondI(expr.VarE("v:main:b", Info(Loc(11,9))), "2IfTrue", "2IfFalse", Info(Loc(11,5))),
            instr.LabelI("2IfTrue"),
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(12,7))), expr.LitE(10, Info(Loc(12,11))), Info(Loc(12,7))),
            instr.GotoI("2IfExit"),
            instr.LabelI("2IfFalse"),
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(14,7))), expr.LitE(30, Info(Loc(14,11))), Info(Loc(14,7))),
            instr.LabelI("2IfExit"),
            instr.GotoI("1WhileCond"),
            instr.LabelI("1WhileExit"),
            instr.ReturnI(expr.VarE("v:main:a", Info(Loc(17,10))), Info(Loc(17,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
