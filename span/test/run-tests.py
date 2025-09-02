#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse

def find_lit():
    """Find the lit.py script."""
    # Try to find lit in common locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'third_party', 'llvm', 'utils', 'lit', 'lit.py'),
        '/usr/lib/llvm-*/share/llvm/lit.py',
        '/usr/lib/llvm-*/build/utils/lit/lit.py',
        '/usr/local/lib/llvm*/share/llvm/lit.py',
        '/opt/llvm*/share/llvm/lit.py',
    ]
    
    for path in possible_paths:
        if '*' in path:
            import glob
            matches = glob.glob(path)
            if matches:
                return matches[0]
        elif os.path.exists(path):
            return path
    
    # Try to find lit via pip
    try:
        result = subprocess.run(['python3', '-m', 'lit', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return 'python3 -m lit'
    except:
        pass
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Run Span tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--filter', '-f', type=str,
                       help='Filter tests by pattern')
    parser.add_argument('--jobs', '-j', type=int, default=1,
                       help='Number of parallel jobs')
    parser.add_argument('--build-dir', type=str, default='built/rel',
                       help='Build directory')
    
    args = parser.parse_args()
    
    # Find lit
    lit_path = find_lit()
    if not lit_path:
        print("Error: Could not find lit.py. Please install LLVM or lit.")
        sys.exit(1)
    
    # Set up environment
    span_obj_root = os.path.abspath(args.build_dir)
    test_dir = os.path.dirname(__file__)
    
    # Build lit command
    cmd = [lit_path, test_dir]
    
    if args.verbose:
        cmd.append('--verbose')
    
    if args.filter:
        cmd.extend(['--filter', args.filter])
    
    if args.jobs > 1:
        cmd.extend(['--jobs', str(args.jobs)])
    
    # Set environment variables
    env = os.environ.copy()
    env['SPAN_OBJ_ROOT'] = span_obj_root
    
    # Run tests
    print(f"Running tests with command: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    
    sys.exit(result.returncode)

if __name__ == '__main__':
    main() 