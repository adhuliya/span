
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
  name = "spanTest155.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:3t": types.Ptr(to=types.Struct("s:Record1")),
    "v:main:2t": types.Ptr(to=types.Struct("s:Record1")),
    "v:main:r0": types.Struct("s:Record0"),
    "v:main:x": types.Ptr(to=types.Struct("s:Record0")),
    "v:main:r1": types.Struct("s:Record1"),
    "v:main:a": types.Int32,
    "v:main:p": types.Ptr(to=types.Int32),
    "v:main:1t": types.Ptr(to=types.Struct("s:Record1")),
  }, # end allVars dict

  globalInits = [
  ], # end globalInits.

  allRecords = {
    "s:Record1":
      types.Struct(
        name = "s:Record1",
        members = [
          ("z", types.Int32),
        ],
        info = Info(Loc(3,1)),
      ),

    "s:Record0":
      types.Struct(
        name = "s:Record0",
        members = [
          ("y", types.Ptr(to=types.Struct("s:Record1"))),
        ],
        info = Info(Loc(7,1)),
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
            instr.AssignI(expr.VarE("v:main:1t", Info(Loc(17,10))), expr.AddrOfE(expr.VarE("v:main:r1", Info(Loc(17,11))), Info(Loc(17,10))), Info(Loc(17,10))),
            instr.AssignI(expr.MemberE("y", expr.VarE("v:main:r0", Info(Loc(17,3))), Info(Loc(17,3))), expr.VarE("v:main:1t", Info(Loc(17,10))), Info(Loc(17,3))),
            instr.AssignI(expr.VarE("v:main:2t", Info(Loc(18,3))), expr.MemberE("y", expr.VarE("v:main:r0", Info(Loc(18,3))), Info(Loc(18,3))), Info(Loc(18,3))),
            instr.AssignI(expr.MemberE("z", expr.VarE("v:main:2t", Info(Loc(18,3))), Info(Loc(18,3))), expr.LitE(20, Info(Loc(18,13))), Info(Loc(18,3))),
            instr.AssignI(expr.VarE("v:main:x", Info(Loc(20,3))), expr.AddrOfE(expr.VarE("v:main:r0", Info(Loc(20,8))), Info(Loc(20,7))), Info(Loc(20,3))),
            instr.AssignI(expr.VarE("v:main:3t", Info(Loc(21,8))), expr.MemberE("y", expr.VarE("v:main:x", Info(Loc(21,8))), Info(Loc(21,8))), Info(Loc(21,8))),
            instr.AssignI(expr.VarE("v:main:p", Info(Loc(21,3))), expr.AddrOfE(expr.MemberE("z", expr.VarE("v:main:3t", Info(Loc(21,8))), Info(Loc(21,8))), Info(Loc(21,7))), Info(Loc(21,3))),
            instr.AssignI(expr.VarE("v:main:a", Info(Loc(23,3))), expr.DerefE(expr.VarE("v:main:p", Info(Loc(23,8))), Info(Loc(23,7))), Info(Loc(23,3))),
            instr.ReturnI(expr.VarE("v:main:a", Info(Loc(25,10))), Info(Loc(25,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
