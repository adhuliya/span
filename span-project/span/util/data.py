#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""Project wide messages / strings.."""

START_BB_ID_NOT_MINUS_ONE = (
  "Start BB id is not -1 in the given input"
  "Dict[BasicBlockId, BB]."
)

END_BB_ID_NOT_ZERO = (
  "End BB id is not 0 in the given input Dict[BasicBlockId, BB]."
  "\nThis is required if BB count is greater than one."
)

PTR_INDLEV_INVALID = "Indirection level of pointer is less than 1!"
TOP_BOT_BOTH = "Are you saying its Top and Bot at the same time?!!!"

SHOULD_BE_ONLY_ONE_EDGE = "There should be only one edge here."

MSG_C2SPANIR_FAILED = ("The conversion of C file '{cFileName}' to SPANIR failed."
                       "The command used was:\n  {cmd}")

################################################
# BOUND START: for_span_testing_module
################################################

FAIL_C_TEST_FILES_NOT_PRESENT = "Current dir contains no test files."
FAIL_C_RESULT_FILES_NOT_PRESENT = "Current dir contains no result files."
FAIL_NO_C2SPANIR_SUPPORT = "`clang` compiler in path, has no SPAN support."
FAIL_NO_CLANG_IN_PATH = "`clang` compiler not in path"

################################################
# BOUND END  : for_span_testing_module
################################################


################################################
# BOUND START: for_span_testing_module
################################################

# usage: CMD_F_GEN_SPANIR.format(cFileName="test.c")
CMD_F_GEN_SPANIR = ("clang --analyze -Xanalyzer"
                   " -analyzer-checker=core.span.SlangGenAst {cFileName}")

CMD_F_SLANG_BUG = ("scan-build -V"
                   # " -analyzer-disable-all-checks"
                   # " -disable-checker security.insecureAPI.vfork"
                   " -enable-checker core.span.SlangBug "
                   " clang -c -std=c99 {includesString} {cFileName}")
################################################
# BOUND END  : for_span_testing_module
################################################

# DISABLE_CHECKER_STRING =

NUM_STR = "Num"
PTR_STR = "Ptr"
RECORD_STR = "Record"

ASSIGN_I_STR = "Assign"  # _I_ stands for Instruction
NOP_I_STR = "Nop"
BARRIER_I_STR = "Barrier"
USE_STR = "Use"
EXREAD_I_STR = "ExRead"
CONDREAD_I_STR = "CondRead"
UNDEFVAL_I_STR = "UnDefVal"
FILTER_I_STR = "Filter"
CALL_I_STR = "Call"
RETURN_I_STR = "Return"
COND_I_STR = "Conditional"
GOTO_I_STR = "Goto"  # added for completeness
LABEL_I_STR = "Label"  # added for completeness
PARALLEL_I_STR = "Parallel"  # added for completeness

LIT_E_STR = "Lit"  # _E_ stands for Expression
VAR_E_STR = "Var"
FUNCNAME_E_STR = "FuncName"
SIZEOF_E_STR = "SizeOf"
UNARYARITH_E_STR = "UnaryArith"
BINARYARITH_E_STR = "BinArith"
DEREF_E_STR = "Deref"
ARRAY_E_STR = "Array"
MEMBER_E_STR = "Member"
SELECT_E_STR = "Select"
CALL_E_STR = "Call"
CASTVAR_E_STR = "CastVar"
CASTARR_E_STR = "CastArr"
ADDROFVAR_E_STR = "AddrOfVar"
ADDROFARRAY_E_STR = "AddrOfArray"
ADDROFMEMBER_E_STR = "AddrOfMember"
ADDROFDEREF_E_STR = "AddrOfDeref"
ADDROFFUNC_E_STR = "AddrOfFunc"
ALLOC_E_STR = "Alloc"  # added for completeness
PHI_E_STR = "Phi"  # added for completeness


