
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
  name = "spanTest012.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:3t": types.Ptr(to=types.Int32),
    "v:main:2t": types.Ptr(to=types.Int32),
    "v:main:1if": types.Int32,
    "v:main:y": types.Ptr(to=types.Int32),
    "v:main:b": types.Int32,
    "v:main:a": types.Int32,
    "v:main:w": types.Ptr(to=types.Ptr(to=types.Int32)),
    "v:main:z": types.Ptr(to=types.Ptr(to=types.Int32)),
    "v:main:c": types.Int32,
    "v:main:x": types.Ptr(to=types.Int32),
    "v:main:i": types.Int32,
    "v:main:e": types.Int32,
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
            instr.AssignI(expr.VarE("v:main:x", Info(Loc(5,3))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(5,8))), Info(Loc(5,7))), Info(Loc(5,3))),
            instr.AssignI(expr.VarE("v:main:y", Info(Loc(6,3))), expr.AddrOfE(expr.VarE("v:main:b", Info(Loc(6,8))), Info(Loc(6,7))), Info(Loc(6,3))),
            instr.AssignI(expr.VarE("v:main:w", Info(Loc(7,3))), expr.AddrOfE(expr.VarE("v:main:y", Info(Loc(7,8))), Info(Loc(7,7))), Info(Loc(7,3))),
            instr.AssignI(expr.VarE("v:main:1if", Info(Loc(9,7))), expr.BinaryE(expr.VarE("v:main:i", Info(Loc(9,7))), op.BO_LT, expr.LitE(0, Info(Loc(9,11))), Info(Loc(9,7))), Info(Loc(9,7))),
            instr.CondI(expr.VarE("v:main:1if", Info(Loc(9,7))), "1IfTrue", "1IfFalse", Info(Loc(9,3))),
            instr.LabelI("1IfTrue"),
            instr.AssignI(expr.VarE("v:main:z", Info(Loc(10,5))), expr.AddrOfE(expr.VarE("v:main:x", Info(Loc(10,10))), Info(Loc(10,9))), Info(Loc(10,5))),
            instr.GotoI("1IfExit"),
            instr.LabelI("1IfFalse"),
            instr.AssignI(expr.VarE("v:main:z", Info(Loc(12,5))), expr.AddrOfE(expr.VarE("v:main:y", Info(Loc(12,10))), Info(Loc(12,9))), Info(Loc(12,5))),
            instr.LabelI("1IfExit"),
            instr.AssignI(expr.VarE("v:main:2t", Info(Loc(15,8))), expr.AddrOfE(expr.VarE("v:main:e", Info(Loc(15,9))), Info(Loc(15,8))), Info(Loc(15,8))),
            instr.AssignI(expr.DerefE(expr.VarE("v:main:z", Info(Loc(15,4))), Info(Loc(15,3))), expr.VarE("v:main:2t", Info(Loc(15,8))), Info(Loc(15,3))),
            instr.AssignI(expr.VarE("v:main:3t", Info(Loc(16,8))), expr.AddrOfE(expr.VarE("v:main:e", Info(Loc(16,9))), Info(Loc(16,8))), Info(Loc(16,8))),
            instr.AssignI(expr.DerefE(expr.VarE("v:main:w", Info(Loc(16,4))), Info(Loc(16,3))), expr.VarE("v:main:3t", Info(Loc(16,8))), Info(Loc(16,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
