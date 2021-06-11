#!/usr/bin/env python3

# MIT License
# Copyright (C) 2021 Anshuman Dhuliya

"""
The basic tests necessary to run SPAN.
"""

import unittest
import subprocess as subp
import span.util.consts as consts
import span.tests.common as common


class SpanBasicTests(unittest.TestCase):


  def setUp(self):
    # called before every test function
    pass


  def tearDown(self):
    # called after every test function
    pass


  def test_AABA_dummy(self):
    self.assertEqual(2, 2)


  def test_AACA_isCwdATestDirectory(self):
    """Does current directory contain the test and result files?"""

    print("\nTest: Curr Directory is a test directory? START.\n")
    status, cfiles = \
      subp.getstatusoutput("ls spanTest[0-9][0-9][0-9].c")
    self.assertEqual(status, 0, consts.FAIL_C_TEST_FILES_NOT_PRESENT)

    status, resultFiles = \
      subp.getstatusoutput("ls spanTest[0-9][0-9][0-9].c.results.py")
    self.assertEqual(status, 0, consts.FAIL_C_RESULT_FILES_NOT_PRESENT)
    print("\nTest: Curr Directory is a test directory? END.\n")


  def test_AADA_isClangInPathAndSpanEnabled(self):
    """Is there a clang compiler in the current path? (False: if an error)
    Does clang support SpanIr conversion? (False: if an error)"""
    print("\nTest: Is 'clang' in path? START.\n")
    status, output = subp.getstatusoutput("clang")
    if status != 1: common.SPAN_LLVM_AVAILABLE = False
    self.assertEqual(status, 1, consts.FAIL_NO_CLANG_IN_PATH)
    print("\nTest: Is 'clang' in path? END.\n")

    # Does clang support SpanIr conversion? (False: if an error)
    print("\nTest: Can 'clang' convert C(ClangAST) to SPANIR? START.\n")
    cmd = ("""echo "int main(){}" | clang -x c """
           "--analyze -Xanalyzer -analyzer-checker=core.span.SlangGenAst -")
    status, output = subp.getstatusoutput(cmd)
    if status != 0: common.SPAN_LLVM_AVAILABLE = False
    self.assertEqual(status, 0, consts.FAIL_NO_C2SPANIR_SUPPORT)
    print("\nTest: Can 'clang' convert C(ClangAST) to SPANIR? END.\n")


def runTests():
  """Call this function to start tests."""
  print("\nTesting basic requirements now.")
  suite = unittest.TestSuite()
  for name, nameType in SpanBasicTests.__dict__.items():
    if callable(nameType) and name.startswith("test_"):
      suite.addTest(SpanBasicTests(name))
  runner = unittest.TextTestRunner()
  runner.run(suite)
  # unittest.main(SpanTestBasic())


def addTests(suite: unittest.TestSuite) -> None:
  """Call this function to add tests."""
  for name, nameType in SpanBasicTests.__dict__.items():
    if callable(nameType) and name.startswith("test_"):
      suite.addTest(SpanBasicTests(name))
  return None


if __name__ == "__main__":
  # unittest.main()
  runTests()
