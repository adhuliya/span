
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
  name = "spanTest016.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:1if": types.Int32,
    "v:main:a": types.Int32,
    "v:main:c": types.Ptr(to=types.Int32),
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
            instr.AssignI(expr.VarE("v:main:c", Info(Loc(3,3))), expr.LitE(0, Info(Loc(3,7))), Info(Loc(3,3))),
            instr.AssignI(expr.VarE("v:main:1if", Info(Loc(4,7))), expr.BinaryE(expr.VarE("v:main:c", Info(Loc(4,7))), op.BO_NE, expr.LitE(0, Info(Loc(4,12))), Info(Loc(4,7))), Info(Loc(4,7))),
            instr.CondI(expr.VarE("v:main:1if", Info(Loc(4,7))), "1IfTrue", "1IfFalse", Info(Loc(4,3))),
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

# END  : A_SPAN_translation_unit!
