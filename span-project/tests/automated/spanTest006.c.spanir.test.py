
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
  name = "spanTest006.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:c": types.Int32,
    "v:main:b": types.Int32,
    "v:main:p": types.Ptr(to=types.Int32),
    "v:main:argc": types.Int32,
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
        paramNames = ["v:main:argc"],
        variadic = False,
        returnType = types.Int32,

        instrSeq = [
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(5,3))), expr.LitE(10, Info(Loc(5,7))), Info(Loc(5,3))),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(6,3))), expr.LitE(20, Info(Loc(6,7))), Info(Loc(6,3))),
            instr.CondI(expr.VarE("v:main:a", Info(Loc(8,7))), "1IfTrue", "1IfFalse", Info(Loc(8,3))),
            instr.LabelI("1IfTrue"),
            instr.AssignI(expr.VarE("v:main:p", Info(Loc(9,5))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(9,10))), Info(Loc(9,9))), Info(Loc(9,5))),
            instr.GotoI("1IfExit"),
            instr.LabelI("1IfFalse"),
            instr.AssignI(expr.VarE("v:main:p", Info(Loc(11,5))), expr.AddrOfE(expr.VarE("v:main:b", Info(Loc(11,10))), Info(Loc(11,9))), Info(Loc(11,5))),
            instr.LabelI("1IfExit"),
            instr.AssignI(expr.VarE("v:main:c", Info(Loc(14,3))), expr.DerefE(expr.VarE("v:main:p", Info(Loc(14,8))), Info(Loc(14,7))), Info(Loc(14,3))),
            instr.ReturnI(expr.VarE("v:main:c", Info(Loc(15,10))), Info(Loc(15,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
