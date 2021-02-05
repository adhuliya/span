
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
  name = "spanTest105.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:1t": types.Int32,
    "v:main:n1": types.Struct("s:Node"),
    "v:main:n2": types.Struct("s:Node"),
  }, # end allVars dict

  globalInits = [
  ], # end globalInits.

  allRecords = {
    "s:Node":
      types.Struct(
        name = "s:Node",
        members = [
          ("val", types.Int32),
          ("next", types.Ptr(to=types.Struct("s:Node"))),
        ],
        info = Info(Loc(1,1)),
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
            instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n1", Info(Loc(8,3))), Info(Loc(8,3))), expr.LitE(10, Info(Loc(8,12))), Info(Loc(8,3))),
            instr.AssignI(expr.VarE("v:main:n2", Info(Loc(9,3))), expr.VarE("v:main:n1", Info(Loc(9,8))), Info(Loc(9,3))),
            instr.AssignI(expr.VarE("v:main:1t", Info(Loc(10,10))), expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(10,10))), Info(Loc(10,10))), Info(Loc(10,10))),
            instr.ReturnI(expr.VarE("v:main:1t", Info(Loc(10,10))), Info(Loc(10,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
