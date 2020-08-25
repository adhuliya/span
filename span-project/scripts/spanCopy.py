#!/usr/bin/env python3

# Copy span for span's clone repo at git.cse.iitb.ac.in
# It copyies all the relevant files (with full source) to run the project.

# Note that now I don't compile any python module.
# Q. How to compile a python module?
#   import py_compile as pyc
#   pyc.compile("span/sys/host.py", optimize=2)

import os
import sys
import subprocess as subp
import py_compile as pyc

CURR_DIR = os.getcwd()
DEST_DIR = "/home/codeman/.itsoflife/mydata/git/research/code/SPAN-CS614-Spring-2019-git"

def runCmd(cmd: str, suppressError=False):
  print("Running:", cmd)
  ret = subp.getstatusoutput(cmd) 
  if ret[0] != 0 and not suppressError:
    print(ret[1], file=sys.stderr)
    exit()

# Skipping the STEP 1, since now I copy complete source files.
## STEP 1: compile and copy the span.host package first
## STEP 1.1: compile all files in package span.sys
#for fileName in os.listdir("span/sys"):
#  if fileName.endswith(".py"):
#    ret = pyc.compile("span/sys/" + fileName, optimize=2)
#    print(f"Compiling {fileName}:", ret)
##STEP 1.2: copy all compiled files
#for fileName in os.listdir("span/sys/__pycache__"):
#  if fileName.endswith("opt-2.pyc"):
#    # rename to a simple name e.g. host.pyc
#    newFileName = fileName.split(".")[0] + ".pyc"
#    destDir = DEST_DIR + "span/sys"
#    runCmd(f"mkdir -p {destDir}")
#    runCmd(f"cp span/sys/__pycache__/{fileName} {destDir}/{newFileName}")

# STEP 2: copy the files
# STEP 2.01: delete all the contents of the dest dir
runCmd(f"rm -Rf {DEST_DIR}/*", True)

# STEP 2.1: copy the top level files
runCmd(f"cp README.md {DEST_DIR}")
runCmd(f"cp LICENSE {DEST_DIR}")
runCmd(f"cp main.py {DEST_DIR}")
runCmd(f"cp -r tests {DEST_DIR}")
runCmd(f"cp cython_compile.py {DEST_DIR}")
#runCmd(f"cp package.sh {DEST_DIR}")
#runCmd(f"cp clean.sh {DEST_DIR}")

# STEP 2.2: copy the python files
walkDir = "span"
for dirPath, dirs, files in os.walk(walkDir):
  if dirPath.endswith("__pycache__"):
    continue
  # Commented since we need the complete source.
  # if dirPath.endswith("span/sys"):
  #   continue
  for fileName in files:
    if fileName.endswith(".py"):
      destDir = f"{DEST_DIR}/{dirPath}"
      runCmd(f"mkdir -p {destDir}")
      filePath = f"{dirPath}/{fileName}"
      runCmd(f"cp {filePath} {destDir}")

print("Done!")


