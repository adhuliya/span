
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
  name = "spanTest210.c",
  description = "Auto-Translated from Clang AST.",

  allVars = {
    "v:main:4t": types.Ptr(to=types.Struct("s:Node")),
    "v:main:2t": types.Ptr(to=types.Void),
    "v:malloc:__size": types.UInt64,
    "v:main:head": types.Ptr(to=types.Struct("s:Node")),
    "v:main:3t": types.Ptr(to=types.Struct("s:Node")),
    "g:stderr": types.Ptr(to=types.Struct("s:_IO_FILE")),
    "g:__morecore": types.Ptr(to=types.FuncSig(returnType=types.Ptr(to=types.Void), paramTypes=[types.Int64])),
    "g:_IO_2_1_stderr_": types.Struct("s:_IO_FILE_plus"),
    "g:stdin": types.Ptr(to=types.Struct("s:_IO_FILE")),
    "g:_IO_2_1_stdout_": types.Struct("s:_IO_FILE_plus"),
    "v:main:1t": types.UInt64,
    "g:sys_errlist": types.IncompleteArray(of=types.Ptr(to=types.Int8)),
    "v:main:n1": types.Struct("s:Node"),
    "v:main:n2": types.Struct("s:Node"),
    "g:_IO_2_1_stdin_": types.Struct("s:_IO_FILE_plus"),
    "g:sys_nerr": types.Int32,
    "g:__after_morecore_hook": types.Ptr(to=types.FuncSig(returnType=types.Void, paramTypes=[])),
    "g:__free_hook": types.Ptr(to=types.FuncSig(returnType=types.Void, paramTypes=[types.Ptr(to=types.Void), types.Ptr(to=types.Void)])),
    "g:__malloc_hook": types.Ptr(to=types.FuncSig(returnType=types.Ptr(to=types.Void), paramTypes=[types.UInt64, types.Ptr(to=types.Void)])),
    "g:__realloc_hook": types.Ptr(to=types.FuncSig(returnType=types.Ptr(to=types.Void), paramTypes=[types.Ptr(to=types.Void), types.UInt64, types.Ptr(to=types.Void)])),
    "g:stdout": types.Ptr(to=types.Struct("s:_IO_FILE")),
    "g:__memalign_hook": types.Ptr(to=types.FuncSig(returnType=types.Ptr(to=types.Void), paramTypes=[types.UInt64, types.UInt64, types.Ptr(to=types.Void)])),
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
        info = Info(Loc(3,1)),
      ),

    "s:_IO_marker":
      types.Struct(
        name = "s:_IO_marker",
        members = [
          ("_next", types.Ptr(to=types.Struct("s:_IO_marker"))),
          ("_sbuf", types.Ptr(to=types.Struct("s:_IO_FILE"))),
          ("_pos", types.Int32),
        ],
        info = Info(Loc(160,1)),
      ),

    "s:_IO_FILE_plus":
      types.Struct(
        name = "s:_IO_FILE_plus",
        members = [
        ],
        info = Info(Loc(317,1)),
      ),

    "s:_IO_FILE":
      types.Struct(
        name = "s:_IO_FILE",
        members = [
          ("_flags", types.Int32),
          ("_IO_read_ptr", types.Ptr(to=types.Int8)),
          ("_IO_read_end", types.Ptr(to=types.Int8)),
          ("_IO_read_base", types.Ptr(to=types.Int8)),
          ("_IO_write_base", types.Ptr(to=types.Int8)),
          ("_IO_write_ptr", types.Ptr(to=types.Int8)),
          ("_IO_write_end", types.Ptr(to=types.Int8)),
          ("_IO_buf_base", types.Ptr(to=types.Int8)),
          ("_IO_buf_end", types.Ptr(to=types.Int8)),
          ("_IO_save_base", types.Ptr(to=types.Int8)),
          ("_IO_backup_base", types.Ptr(to=types.Int8)),
          ("_IO_save_end", types.Ptr(to=types.Int8)),
          ("_markers", types.Ptr(to=types.Struct("s:_IO_marker"))),
          ("_chain", types.Ptr(to=types.Struct("s:_IO_FILE"))),
          ("_fileno", types.Int32),
          ("_flags2", types.Int32),
          ("_old_offset", types.Int64),
          ("_cur_column", types.UInt16),
          ("_vtable_offset", types.Int8),
          ("_shortbuf", types.ConstSizeArray(of=types.Int8, size=1)),
          ("_lock", types.Ptr(to=types.Void)),
          ("_offset", types.Int64),
          ("__pad1", types.Ptr(to=types.Void)),
          ("__pad2", types.Ptr(to=types.Void)),
          ("__pad3", types.Ptr(to=types.Void)),
          ("__pad4", types.Ptr(to=types.Void)),
          ("__pad5", types.UInt64),
          ("_mode", types.Int32),
          ("_unused2", types.ConstSizeArray(of=types.Int8, size=20)),
        ],
        info = Info(Loc(245,1)),
      ),

  }, # end allRecords dict

  allFunctions = {
    "f:malloc":
      constructs.Func(
        name = "f:malloc",
        paramNames = ["v:malloc:__size"],
        variadic = False,
        returnType = types.Ptr(to=types.Void),

        instrSeq = [
        ], # instrSeq end.
      ), # f:malloc() end. 

    "f:main":
      constructs.Func(
        name = "f:main",
        paramNames = [],
        variadic = False,
        returnType = types.Int32,

        instrSeq = [
            instr.AssignI(expr.VarE("v:main:1t", Info(Loc(11,31))), expr.BinaryE(expr.LitE(16, Info(Loc(11,31))), op.BO_MUL, expr.LitE(10, Info(Loc(11,52))), Info(Loc(11,31))), Info(Loc(11,31))),
            instr.AssignI(expr.VarE("v:main:2t", Info(Loc(11,24))), expr.CallE(expr.VarE("f:malloc", Info(Loc(11,24))), [expr.VarE("v:main:1t", Info(Loc(11,31)))], Info(Loc(11,24))), Info(Loc(11,24))),
            instr.AssignI(expr.VarE("v:main:head", Info(Loc(11,3))), expr.CastE(expr.VarE("v:main:2t", Info(Loc(11,24))), types.Ptr(to=types.Struct("s:Node")), Info(Loc(11,10))), Info(Loc(11,3))),
            instr.AssignI(expr.VarE("v:main:3t", Info(Loc(12,16))), expr.AddrOfE(expr.VarE("v:main:n1", Info(Loc(12,17))), Info(Loc(12,16))), Info(Loc(12,16))),
            instr.AssignI(expr.MemberE("next", expr.VarE("v:main:head", Info(Loc(12,3))), Info(Loc(12,3))), expr.VarE("v:main:3t", Info(Loc(12,16))), Info(Loc(12,3))),
            instr.AssignI(expr.VarE("v:main:4t", Info(Loc(13,16))), expr.AddrOfE(expr.VarE("v:main:n2", Info(Loc(13,17))), Info(Loc(13,16))), Info(Loc(13,16))),
            instr.AssignI(expr.MemberE("next", expr.VarE("v:main:head", Info(Loc(13,3))), Info(Loc(13,3))), expr.VarE("v:main:4t", Info(Loc(13,16))), Info(Loc(13,3))),
            instr.ReturnI(expr.LitE(0, Info(Loc(14,10))), Info(Loc(14,3))),
        ], # instrSeq end.
      ), # f:main() end. 

  }, # end allFunctions dict

) # tunit.TranslationUnit() ends

# END  : A_SPAN_translation_unit!