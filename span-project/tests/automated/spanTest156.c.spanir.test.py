
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
  name = "spanTest156.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:3t": types.Int32,
    "v:main:1t": types.Ptr(to=types.Int32),
    "v:main:arr": types.ConstSizeArray(of=types.ConstSizeArray(of=types.Int32, size=10), size=10),
    "v:main:2t": types.Ptr(to=types.Int32),
    "v:main:p": types.Ptr(to=types.Int32),
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
            instr.AssignI(expr.VarE("v:main:1t", Info(Loc(7,8))), expr.ArrayE(expr.LitE(5, Info(Loc(7,12))), expr.VarE("v:main:arr", Info(Loc(7,8))), Info(Loc(7,8))), Info(Loc(7,8))),
            instr.AssignI(expr.VarE("v:main:p", Info(Loc(7,3))), expr.AddrOfE(expr.ArrayE(expr.LitE(5, Info(Loc(7,15))), expr.VarE("v:main:1t", Info(Loc(7,8))), Info(Loc(7,8))), Info(Loc(7,7))), Info(Loc(7,3))),
            instr.AssignI(expr.DerefE(expr.VarE("v:main:p", Info(Loc(8,4))), Info(Loc(8,3))), expr.LitE(11, Info(Loc(8,8))), Info(Loc(8,3))),
            instr.AssignI(expr.VarE("v:main:2t", Info(Loc(10,10))), expr.ArrayE(expr.LitE(5, Info(Loc(10,14))), expr.VarE("v:main:arr", Info(Loc(10,10))), Info(Loc(10,10))), Info(Loc(10,10))),
            instr.AssignI(expr.VarE("v:main:3t", Info(Loc(10,10))), expr.ArrayE(expr.LitE(5, Info(Loc(10,17))), expr.VarE("v:main:2t", Info(Loc(10,10))), Info(Loc(10,10))), Info(Loc(10,10))),
            instr.ReturnI(expr.VarE("v:main:3t", Info(Loc(10,10))), Info(Loc(10,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
