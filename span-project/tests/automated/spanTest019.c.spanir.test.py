
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
  name = "spanTest019.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:i": types.Int32,
    "v:main:1if": types.Int32,
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
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(5,3))), expr.LitE(0, Info(Loc(5,7))), Info(Loc(5,3))),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(6,3))), expr.LitE(20, Info(Loc(6,7))), Info(Loc(6,3))),
            instr.AssignI(expr.VarE("v:main:i", Info(Loc(7,7))), expr.LitE(0, Info(Loc(7,9))), Info(Loc(7,7))),
            instr.LabelI("1ForCond"),
            instr.AssignI(expr.VarE("v:main:1if", Info(Loc(7,11))), expr.BinaryE(expr.VarE("v:main:i", Info(Loc(7,11))), op.BO_LT, expr.VarE("v:main:b", Info(Loc(7,13))), Info(Loc(7,11))), Info(Loc(7,11))),
            instr.CondI(expr.VarE("v:main:1if", Info(Loc(7,11))), "1ForBody", "1ForExit", Info(Loc(7,11))),
            instr.LabelI("1ForBody"),
            instr.CondI(expr.VarE("v:main:a", Info(Loc(8,8))), "2IfTrue", "2IfFalse", Info(Loc(8,5))),
            instr.LabelI("2IfTrue"),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(9,7))), expr.LitE(10, Info(Loc(9,11))), Info(Loc(9,7))),
            instr.GotoI("2IfExit"),
            instr.LabelI("2IfFalse"),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(11,7))), expr.LitE(0, Info(Loc(11,11))), Info(Loc(11,7))),
            instr.LabelI("2IfExit"),
            instr.GotoI("1ForCond"),
            instr.LabelI("1ForExit"),
            instr.ReturnI(expr.VarE("v:main:b", Info(Loc(13,10))), Info(Loc(13,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
