
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
  name = "spanTest011.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:1if": types.Int32,
    "v:main:argv": types.Ptr(to=types.Ptr(to=types.Int8)),
    "v:main:u": types.Ptr(to=types.Int32),
    "v:main:argc": types.Int32,
    "v:main:a": types.Int32,
    "v:main:tmp": types.Int32,
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
        paramNames = ["v:main:argc", "v:main:argv"],
        variadic = False,
        returnType = types.Int32,

        instrSeq = [
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(3,3))), expr.LitE(11, Info(Loc(3,7))), Info(Loc(3,3))),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(4,3))), expr.LitE(13, Info(Loc(4,7))), Info(Loc(4,3))),
            instr.AssignI(expr.VarE("v:main:u", Info(Loc(5,3))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(5,8))), Info(Loc(5,7))), Info(Loc(5,3))),
            instr.LabelI("1WhileCond"),
            instr.AssignI(expr.VarE("v:main:1if", Info(Loc(7,9))), expr.BinaryE(expr.VarE("v:main:argc", Info(Loc(7,9))), op.BO_GT, expr.LitE(0, Info(Loc(7,16))), Info(Loc(7,9))), Info(Loc(7,9))),
            instr.CondI(expr.VarE("v:main:1if", Info(Loc(7,9))), "1WhileBody", "1WhileExit", Info(Loc(7,9))),
            instr.LabelI("1WhileBody"),
            instr.AssignI(expr.VarE("v:main:tmp", Info(Loc(8,5))), expr.DerefE(expr.VarE("v:main:u", Info(Loc(8,12))), Info(Loc(8,11))), Info(Loc(8,5))),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(9,5))), expr.BinaryE(expr.VarE("v:main:tmp", Info(Loc(9,9))), op.BO_MOD, expr.LitE(2, Info(Loc(9,15))), Info(Loc(9,9))), Info(Loc(9,5))),
            instr.CondI(expr.VarE("v:main:b", Info(Loc(10,8))), "2IfTrue", "2IfFalse", Info(Loc(10,5))),
            instr.LabelI("2IfTrue"),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(11,7))), expr.LitE(15, Info(Loc(11,11))), Info(Loc(11,7))),
            instr.GotoI("2IfExit"),
            instr.LabelI("2IfFalse"),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(13,7))), expr.LitE(16, Info(Loc(13,11))), Info(Loc(13,7))),
            instr.LabelI("2IfExit"),
            instr.AssignI(expr.VarE("v:main:u", Info(Loc(15,5))), expr.AddrOfE(expr.VarE("v:main:b", Info(Loc(15,10))), Info(Loc(15,9))), Info(Loc(15,5))),
            instr.AssignI(expr.VarE("v:main:argc", Info(Loc(16,5))), expr.BinaryE(expr.VarE("v:main:argc", Info(Loc(16,5))), op.BO_SUB, expr.LitE(1, Info(Loc(16,13))), Info(Loc(16,5))), Info(Loc(16,5))),
            instr.GotoI("1WhileCond"),
            instr.LabelI("1WhileExit"),
            instr.ReturnI(expr.VarE("v:main:b", Info(Loc(18,10))), Info(Loc(18,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
