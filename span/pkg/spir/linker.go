package spir

// This file defines the logic to link two Translation Units together.

// LinkTUs links a list of translation units together.
// It creates a new translation unit that is the "union" of all the translation units in the given list.
// It puts all the functions, data types and variables from the given TUs to the new TU.
// It returns the new translation unit instance (or the first TU if modifyFirstTU is true).
func LinkTUs(tuList []*TU, context *Context, modifyFirstTU bool) *TU {
	var newTU *TU
	if modifyFirstTU {
		newTU = tuList[0]
	} else {
		newTU = NewTU()
	}

	// Add linking logic here

	return newTU
}
