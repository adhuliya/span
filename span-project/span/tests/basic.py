#!/usr/bin/env python3

# MIT License
# Copyright (c) 2020 Anshuman Dhuliya

"""
The basic tests necessary to run SPAN.
"""

import unittest
import subprocess as subp
import span.util.data as data


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

    status, cfiles = \
      subp.getstatusoutput("ls spanTest[0-9][0-9][0-9].c")
    self.assertEqual(status, 0, data.FAIL_C_TEST_FILES_NOT_PRESENT)

    status, resultFiles = \
      subp.getstatusoutput("ls spanTest[0-9][0-9][0-9].c.results.py")
    self.assertEqual(status, 0, data.FAIL_C_RESULT_FILES_NOT_PRESENT)


  def test_AADA_isClangInPath(self):
    """Is there a clang compiler in the current path? (False: if an error)"""
    status, output = subp.getstatusoutput("clang")
    self.assertEqual(status, 1, data.FAIL_NO_CLANG_IN_PATH)


  def test_AAEA_isC2spanirPossible(self):
    """Does clang support SpanIr conversion? (False: if an error)"""
    cmd = ("""echo "int main(){}" | clang -x c """
           "--analyze -Xanalyzer -analyzer-checker=core.span.SlangGenAst -")
    status, output = subp.getstatusoutput(cmd)
    self.assertEqual(status, 0, data.FAIL_NO_C2SPANIR_SUPPORT)


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
