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
func NewExampleTU_A() *TU {
	tu := NewTU()

	main := tu.NewFunction(
		"main",
		NewBasicValueType(K_VK_INT32, K_QK_QNONE),
		nil,
		nil)

	x := tu.NewVar("x", K_EK_VAR, NewBasicValueType(K_VK_INT32, K_QK_QNONE), main.id)
	y := tu.NewVar("y", K_EK_VAR, NewBasicValueType(K_VK_INT32, K_QK_QNONE), main.id)
	c10 := tu.NewConst(10, NewBasicValueType(K_VK_INT32, K_QK_QNONE))

	bb := NewBasicBlock(tu.NewBBId(), 0, main.id, 2)
	tu.AddInsn(bb, NewInsnBinOpAssign(x, y, c10, K_XK_ADD))
	tu.AddInsn(bb, NewInsnReturn(x))
	main.body = bb // a single basic block is a Graph

	return tu
}
