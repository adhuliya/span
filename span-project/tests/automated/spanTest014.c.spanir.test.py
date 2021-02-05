
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
  name = "spanTest014.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:x": types.Ptr(to=types.Ptr(to=types.Int32)),
    "v:main:b": types.Ptr(to=types.Int32),
    "v:main:a": types.Int32,
    "v:main:c": types.Ptr(to=types.Int32),
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
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(5,3))), expr.LitE(5, Info(Loc(5,7))), Info(Loc(5,3))),
            instr.AssignI(expr.VarE("v:main:c", Info(Loc(6,3))), expr.AddrOfE(expr.VarE("v:main:a", Info(Loc(6,8))), Info(Loc(6,7))), Info(Loc(6,3))),
            instr.AssignI(expr.VarE("v:main:x", Info(Loc(7,3))), expr.AddrOfE(expr.VarE("v:main:c", Info(Loc(7,8))), Info(Loc(7,7))), Info(Loc(7,3))),
            instr.AssignI(expr.VarE("v:main:b", Info(Loc(8,3))), expr.DerefE(expr.VarE("v:main:x", Info(Loc(8,8))), Info(Loc(8,7))), Info(Loc(8,3))),
            instr.ReturnI(expr.LitE(0, Info(Loc(9,10))), Info(Loc(9,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
