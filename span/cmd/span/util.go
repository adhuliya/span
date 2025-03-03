package main

// A simple monad like function which takes a
//   - a function that takes no argument and returns an error
//   - a error
//
// It runs the function and returns its error only if the given error is nil.
// Otherwise, it returns the given error.
func Run(f func() error, err error) error {
	if err != nil {
		return err
	}
	return f()
}
