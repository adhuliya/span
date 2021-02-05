
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
  name = "spanTest050.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:v": types.Ptr(to=types.Int32),
    "v:main:arr": types.ConstSizeArray(of=types.Int32, size=10),
    "v:main:u": types.Ptr(to=types.Int32),
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
            instr.AssignI(expr.VarE("v:main:u", Info(Loc(6,3))), expr.VarE("v:main:arr", Info(Loc(6,7))), Info(Loc(6,3))),
            instr.AssignI(expr.VarE("v:main:v", Info(Loc(7,3))), expr.AddrOfE(expr.VarE("v:main:arr", Info(Loc(7,8))), Info(Loc(7,7))), Info(Loc(7,3))),
            instr.ReturnI(expr.LitE(0, Info(Loc(8,10))), Info(Loc(8,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
