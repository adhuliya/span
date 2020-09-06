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

################################################
# BOUND END  : for_span_testing_module
################################################

# DISABLE_CHECKER_STRING = "-disable-checker security.insecureAPI.vfork "
