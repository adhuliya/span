
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
  name = "spanTest005.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:example_func_1:1if": types.Int32,
    "v:example_func_1:c": types.Int32,
    "v:example_func_1:d": types.Int32,
    "v:example_func_1:a": types.Int32,
    "v:example_func_1:b": types.Int32,
  }, # end allVars dict

  globalInits = [
  ], # end globalInits.

  allRecords = {
  }, # end allRecords dict

  allFunctions = {
    "f:example_func_1":
      constructs.Func(
        name = "f:example_func_1",
        paramNames = ["v:example_func_1:a"],
        variadic = False,
        returnType = types.Int32,

        instrSeq = [
            instr.AssignI(expr.VarE("v:example_func_1:1if", Info(Loc(7,7))), expr.BinaryE(expr.VarE("v:example_func_1:a", Info(Loc(7,7))), op.BO_GT, expr.LitE(5, Info(Loc(7,11))), Info(Loc(7,7))), Info(Loc(7,7))),
            instr.CondI(expr.VarE("v:example_func_1:1if", Info(Loc(7,7))), "1IfTrue", "1IfFalse", Info(Loc(7,3))),
            instr.LabelI("1IfTrue"),
            instr.AssignI(expr.VarE("v:example_func_1:c", Info(Loc(8,7))), expr.BinaryE(expr.VarE("v:example_func_1:a", Info(Loc(8,11))), op.BO_MOD, expr.LitE(20, Info(Loc(8,15))), Info(Loc(8,11))), Info(Loc(8,7))),
            instr.AssignI(expr.VarE("v:example_func_1:b", Info(Loc(9,7))), expr.LitE(90, Info(Loc(9,11))), Info(Loc(9,7))),
            instr.GotoI("1IfExit"),
            instr.LabelI("1IfFalse"),
            instr.AssignI(expr.VarE("v:example_func_1:c", Info(Loc(11,7))), expr.BinaryE(expr.VarE("v:example_func_1:a", Info(Loc(11,11))), op.BO_MOD, expr.LitE(10, Info(Loc(11,15))), Info(Loc(11,11))), Info(Loc(11,7))),
            instr.AssignI(expr.VarE("v:example_func_1:b", Info(Loc(12,7))), expr.LitE(100, Info(Loc(12,11))), Info(Loc(12,7))),
            instr.LabelI("1IfExit"),
            instr.AssignI(expr.VarE("v:example_func_1:d", Info(Loc(15,3))), expr.BinaryE(expr.VarE("v:example_func_1:c", Info(Loc(15,7))), op.BO_ADD, expr.VarE("v:example_func_1:b", Info(Loc(15,11))), Info(Loc(15,7))), Info(Loc(15,3))),
            instr.CondI(expr.VarE("v:example_func_1:d", Info(Loc(17,7))), "2IfTrue", "2IfFalse", Info(Loc(17,3))),
            instr.LabelI("2IfTrue"),
            instr.AssignI(expr.VarE("v:example_func_1:c", Info(Loc(18,7))), expr.LitE(200, Info(Loc(18,11))), Info(Loc(18,7))),
            instr.GotoI("2IfExit"),
            instr.LabelI("2IfFalse"),
            instr.LabelI("2IfExit"),
            instr.ReturnI(expr.VarE("v:example_func_1:c", Info(Loc(21,10))), Info(Loc(21,3))),
        ], # instrSeq end.
      ), # f:example_func_1() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
