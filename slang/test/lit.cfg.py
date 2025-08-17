# -*- Python -*-

import os
import platform
import subprocess
import tempfile

import lit.formats
import lit.util

from lit.llvm import llvm_config

# Configuration file for the 'slang' test suite.

# name: The name of this test suite.
config.name = 'slang'

# testFormat: The test format to use to interpret tests.
config.test_format = lit.formats.ShTest(execute_external=True)

# suffixes: A list of file extensions to treat as test files.
config.suffixes = ['.c', '.cpp']

# test_source_root: The root path where tests are located.
config.test_source_root = os.path.dirname(__file__)

# test_exec_root: The root path where tests should be run.
config.test_exec_root = os.path.join(config.test_source_root, '.test_output')

# Add the slang binary to the PATH
slang_bin = os.path.join(config.test_source_root, '..', 'built', 'rel', 'slang')
if not os.path.exists(slang_bin):
    lit_config.fatal(f"Tool not found: {slang_bin}")

slang_dbg_bin = os.path.join(config.test_source_root, '..', 'built', 'dbg', 'slang')
if not os.path.exists(slang_dbg_bin):
    lit_config.warning(f"Debug build not found: {slang_dbg_bin}. Using release build.")
    slang_dbg_bin = slang_bin

# Set up the slang tool substitution
config.substitutions.append(('%slang', slang_bin))
config.substitutions.append(('%dslang', slang_dbg_bin))
config.substitutions.append(('%gdb', "/usr/bin/gdb"))

# Get LLVM tool paths
config.clang = lit.util.which('clang')
if not config.clang:
    lit_config.fatal("clang not found")

config.filecheck_path = lit.util.which('FileCheck') 
if not config.filecheck_path:
    lit_config.fatal("FileCheck not found")

config.llvm_as = lit.util.which('llvm-as')
if not config.llvm_as:
    lit_config.fatal("llvm-as not found")

config.llvm_dis = lit.util.which('llvm-dis')
if not config.llvm_dis:
    lit_config.fatal("llvm-dis not found")

# Get LLVM tools directory
config.llvm_tools_dir = os.path.dirname(config.clang)

# Set up other common substitutions
config.substitutions.append(('%clang', config.clang))
config.substitutions.append(('%llvm-as', config.llvm_as))
config.substitutions.append(('%llvm-dis', config.llvm_dis))
config.substitutions.append(('%FileCheck', config.filecheck_path))
config.substitutions.append(('%protoc', "/usr/bin/protoc"))

# Add features for different platforms
if platform.system() == 'Darwin':
    config.available_features.add('system-darwin')
elif platform.system() == 'Linux':
    config.available_features.add('system-linux')
elif platform.system() == 'Windows':
    config.available_features.add('system-windows')

# Add features for different architectures
if platform.machine() == 'x86_64':
    config.available_features.add('x86_64')
elif platform.machine() == 'aarch64':
    config.available_features.add('aarch64')

# Set up the environment for running tests
config.environment['PATH'] = os.pathsep.join((
    config.llvm_tools_dir,
    config.environment.get('PATH', ''),
))

# Set up the environment for slang
config.environment['SLANG_TEST_DIR'] = config.test_source_root

# Add slang-specific features
config.available_features.add('slang-tool') 