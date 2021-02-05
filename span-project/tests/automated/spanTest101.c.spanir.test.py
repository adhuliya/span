
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
  name = "spanTest101.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:5t": types.Int32,
    "v:main:4t": types.Ptr(to=types.Struct("s:node")),
    "v:main:n": types.Struct("s:node"),
    "v:main:arr": types.ConstSizeArray(of=types.Struct("s:node"), size=10),
    "v:main:1t": types.Ptr(to=types.Struct("s:node")),
    "v:main:n1": types.Struct("s:node"),
    "v:main:2t": types.Ptr(to=types.Struct("s:node")),
    "v:main:3t": types.Ptr(to=types.Struct("s:node")),
  }, # end allVars dict

  globalInits = [
  ], # end globalInits.

  allRecords = {
    "s:node":
      types.Struct(
        name = "s:node",
        members = [
          ("val", types.Int32),
          ("next", types.Ptr(to=types.Struct("s:node"))),
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
            instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n", Info(Loc(9,3))), Info(Loc(9,3))), expr.LitE(10, Info(Loc(9,11))), Info(Loc(9,3))),
            instr.AssignI(expr.VarE("v:main:1t", Info(Loc(10,3))), expr.AddrOfE(expr.ArrayE(expr.LitE(5, Info(Loc(10,7))), expr.VarE("v:main:arr", Info(Loc(10,3))), Info(Loc(10,3))), Info(Loc(10,3))), Info(Loc(10,3))),
            instr.AssignI(expr.VarE("v:main:2t", Info(Loc(10,17))), expr.AddrOfE(expr.VarE("v:main:n", Info(Loc(10,18))), Info(Loc(10,17))), Info(Loc(10,17))),
            instr.AssignI(expr.MemberE("next", expr.VarE("v:main:1t", Info(Loc(10,3))), Info(Loc(10,3))), expr.VarE("v:main:2t", Info(Loc(10,17))), Info(Loc(10,3))),
            instr.AssignI(expr.VarE("v:main:3t", Info(Loc(11,10))), expr.AddrOfE(expr.ArrayE(expr.LitE(5, Info(Loc(11,14))), expr.VarE("v:main:arr", Info(Loc(11,10))), Info(Loc(11,10))), Info(Loc(11,10))), Info(Loc(11,10))),
            instr.AssignI(expr.VarE("v:main:4t", Info(Loc(11,10))), expr.MemberE("next", expr.VarE("v:main:3t", Info(Loc(11,10))), Info(Loc(11,10))), Info(Loc(11,10))),
            instr.AssignI(expr.VarE("v:main:5t", Info(Loc(11,10))), expr.MemberE("val", expr.VarE("v:main:4t", Info(Loc(11,10))), Info(Loc(11,10))), Info(Loc(11,10))),
            instr.ReturnI(expr.VarE("v:main:5t", Info(Loc(11,10))), Info(Loc(11,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
