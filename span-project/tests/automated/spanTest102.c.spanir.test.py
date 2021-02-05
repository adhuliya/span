
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
  name = "spanTest102.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:3if": types.Int32,
    "v:main:2t": types.Int32,
    "v:main:1if": types.Int32,
    "v:main:u": types.Ptr(to=types.Struct("s:node")),
    "v:main:argv": types.Ptr(to=types.Ptr(to=types.Int8)),
    "v:main:n2": types.Struct("s:node"),
    "v:main:4t": types.Int32,
    "v:main:argc": types.Int32,
    "v:main:a": types.Int32,
    "v:main:n1": types.Struct("s:node"),
    "v:main:tmp": types.Int32,
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
        paramNames = ["v:main:argc", "v:main:argv"],
        variadic = False,
        returnType = types.Int32,

        instrSeq = [
            instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n1", Info(Loc(10,3))), Info(Loc(10,3))), expr.LitE(11, Info(Loc(10,12))), Info(Loc(10,3))),
            instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(11,3))), Info(Loc(11,3))), expr.LitE(13, Info(Loc(11,12))), Info(Loc(11,3))),
            instr.AssignI(expr.VarE("v:main:u", Info(Loc(12,3))), expr.AddrOfE(expr.VarE("v:main:n1", Info(Loc(12,8))), Info(Loc(12,7))), Info(Loc(12,3))),
            instr.LabelI("1WhileCond"),
            instr.AssignI(expr.VarE("v:main:1if", Info(Loc(14,9))), expr.BinaryE(expr.VarE("v:main:argc", Info(Loc(14,9))), op.BO_GT, expr.LitE(0, Info(Loc(14,16))), Info(Loc(14,9))), Info(Loc(14,9))),
            instr.CondI(expr.VarE("v:main:1if", Info(Loc(14,9))), "1WhileBody", "1WhileExit", Info(Loc(14,9))),
            instr.LabelI("1WhileBody"),
            instr.AssignI(expr.VarE("v:main:tmp", Info(Loc(15,5))), expr.MemberE("val", expr.VarE("v:main:u", Info(Loc(15,11))), Info(Loc(15,11))), Info(Loc(15,5))),
            instr.AssignI(expr.VarE("v:main:2t", Info(Loc(16,14))), expr.BinaryE(expr.VarE("v:main:tmp", Info(Loc(16,14))), op.BO_MOD, expr.LitE(2, Info(Loc(16,20))), Info(Loc(16,14))), Info(Loc(16,14))),
            instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(16,5))), Info(Loc(16,5))), expr.VarE("v:main:2t", Info(Loc(16,14))), Info(Loc(16,5))),
            instr.AssignI(expr.VarE("v:main:3if", Info(Loc(17,8))), expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(17,8))), Info(Loc(17,8))), Info(Loc(17,8))),
            instr.CondI(expr.VarE("v:main:3if", Info(Loc(17,8))), "2IfTrue", "2IfFalse", Info(Loc(17,5))),
            instr.LabelI("2IfTrue"),
            instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(18,7))), Info(Loc(18,7))), expr.LitE(15, Info(Loc(18,16))), Info(Loc(18,7))),
            instr.GotoI("2IfExit"),
            instr.LabelI("2IfFalse"),
            instr.AssignI(expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(20,7))), Info(Loc(20,7))), expr.LitE(16, Info(Loc(20,16))), Info(Loc(20,7))),
            instr.LabelI("2IfExit"),
            instr.AssignI(expr.VarE("v:main:u", Info(Loc(22,5))), expr.AddrOfE(expr.VarE("v:main:n2", Info(Loc(22,10))), Info(Loc(22,9))), Info(Loc(22,5))),
            instr.AssignI(expr.VarE("v:main:argc", Info(Loc(23,5))), expr.BinaryE(expr.VarE("v:main:argc", Info(Loc(23,5))), op.BO_SUB, expr.LitE(1, Info(Loc(23,13))), Info(Loc(23,5))), Info(Loc(23,5))),
            instr.GotoI("1WhileCond"),
            instr.LabelI("1WhileExit"),
            instr.AssignI(expr.VarE("v:main:4t", Info(Loc(25,10))), expr.MemberE("val", expr.VarE("v:main:n2", Info(Loc(25,10))), Info(Loc(25,10))), Info(Loc(25,10))),
            instr.ReturnI(expr.VarE("v:main:4t", Info(Loc(25,10))), Info(Loc(25,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
