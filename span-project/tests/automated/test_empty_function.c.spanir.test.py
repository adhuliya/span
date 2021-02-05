
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
  name = "test_empty_function.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
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
        returnType = types.Void,

        instrSeq = [
            instr.NopI(),
        ], # instrSeq end.
      ), # f:main() end. 

    "f:hello":
      constructs.Func(
        name = "f:hello",
        paramNames = [],
        variadic = False,
        returnType = types.Void,

        instrSeq = [
            instr.NopI(),
        ], # instrSeq end.
      ), # f:hello() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!
