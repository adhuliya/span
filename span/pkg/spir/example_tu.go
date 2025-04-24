package spir

// This file defines some example translation units for testing purposes.
// The translation units are simple and represent small real-world programs.
// They are used to test the functionality of the SPAN IR and its components.

// This function creates a simple translation unit for
//
//	int main() {
//	  int x = y + 10;
//	  return x;
//	}
//
// There are no global initializations, so the global function is empty.
// The main function has a single basic block with a single instruction.
func NewExampleTU_A() *TranslationUnit {
	tu := NewTranslationUnit()

	main := tu.NewFunction(
		"main",
		NewBasicValueType(TY_INT32, QUAL_TYPE_NONE),
		nil,
		nil)

	x := tu.NewVar("x", ENTITY_VAR, NewBasicValueType(TY_INT32, QUAL_TYPE_NONE), main.id)
	y := tu.NewVar("y", ENTITY_VAR, NewBasicValueType(TY_INT32, QUAL_TYPE_NONE), main.id)
	c := tu.NewConst(10, NewBasicValueType(TY_INT32, QUAL_TYPE_NONE))

	bb := NewBasicBlock(tu.NewBBId(), 0, main.id, 2)
	tu.AddInsn(bb, NewInsnBinOpAssign(x, y, c, EXPR_BINARY_ADD))
	tu.AddInsn(bb, NewInsnReturn(x))
	main.body = bb // a single basic block is a Graph

	return tu
}
