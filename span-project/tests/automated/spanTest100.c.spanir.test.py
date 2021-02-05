
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
  name = "spanTest100.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:n": types.Struct("s:node"),
    "v:main:1t": types.Ptr(to=types.Struct("s:Node")),
    "v:main:n2": types.Struct("s:node"),
  }, # end allVars dict

  globalInits = [
  ], # end globalInits.

  allRecords = {
    "s:Node":
      types.Struct(
        name = "s:Node",
        members = [
        ],
        info = Info(Loc(3,3)),
      ),

    "s:node":
      types.Struct(
        name = "s:node",
        members = [
          ("val", types.Int32),
          ("next", types.Ptr(to=types.Struct("s:Node"))),
        ],
        info = Info(Loc(1,9)),
      ),

  }, # end allRecords dict

  allFunctions = {
    "f:main":
      constructs.Func(
        name = "f:main",
        paramNames = [],
        variadic = False,
        returnType = types.Int32,

        instrSeq = [
            instr.AssignI(expr.VarE("v:main:1t", Info(Loc(9,12))), expr.AddrOfE(expr.VarE("v:main:n2", Info(Loc(9,13))), Info(Loc(9,12))), Info(Loc(9,12))),
            instr.AssignI(expr.MemberE("next", expr.VarE("v:main:n", Info(Loc(9,3))), Info(Loc(9,3))), expr.VarE("v:main:1t", Info(Loc(9,12))), Info(Loc(9,3))),
            instr.ReturnI(expr.LitE(0, Info(Loc(10,10))), Info(Loc(10,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
