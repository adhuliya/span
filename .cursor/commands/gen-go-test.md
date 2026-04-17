# gen-go-test

Generate the test file for the given go module. Take the following steps.

1.  For the given go file by the user, say abc.go, find the corresponding test file abc_test.go in the same folder.
2. If the test file is not present then create a new test file.
3. Read and analyze the go file that needs testing. Identify the functions that can be tested.
4. Read the test file if it already exists and determine the updates needed to the tests. Always ensure that edge cases are properly covered and updated as per the current go file contents.
5. Fix obvious bugs in the go file that you find during test generation.
6. Run the generated tests on the span project. If possible use `Makefile` to build and test.
7. Fix any bugs found in this process and repeat step 3 until all tests pass with good coverage.

If required add additional functionality to the original go file to help test the feature completely.