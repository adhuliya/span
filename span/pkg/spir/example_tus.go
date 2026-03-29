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

	main := tu.NewFunction("main", NewQualVT(&Int32VT, K_QK_QNIL), nil, nil)

	x := tu.NewVar("x", K_EK_EVAR_LOCL, NIL_ID, main.Id(), NewQualVT(&Int32VT, K_QK_QNIL))
	y := tu.NewVar("y", K_EK_EVAR_LOCL, NIL_ID, main.Id(), NewQualVT(&Int32VT, K_QK_QNIL))
	c10 := tu.NewConst(10, NewQualVT(&Int32VT, K_QK_QNIL))

	bb := NewBasicBlock(tu.GetUniqueBBId(), 0, main.Id(), 2)
	tu.AddInsn(bb, AssignI(ValX(x), BinX(K_XK_XADD, y, c10)), nil)
	tu.AddInsn(bb, ReturnI(ValX(x)), nil)
	main.body = bb // a single basic block is a Graph

	return tu
}

// This function creates a simple translation unit for
//
//	int main(int argc) {
//	  if (argc > 0) {
//	    return 0;
//	  }
//	  return 1;
//	}
//
// All instructions are in a single basic block here.
// For instructions split across multiple basic blocks, see NewExampleTU_B_1.
// This CFG is created automatically for such functions.
func NewExampleTU_B_0() *TU {
	tu := NewTU()

	main := tu.NewFunction("main", NewQualVT(&Int32VT, K_QK_QNIL), nil, nil)

	argc := tu.NewVar("argc", K_EK_EVAR_LOCL, NIL_ID, main.Id(), NewQualVT(&Int32VT, K_QK_QNIL))
	t1 := tu.NewVar("t1", K_EK_EVAR_LOCL_TMP, NIL_ID, main.Id(), NewQualVT(&Int32VT, K_QK_QNIL))
	c0 := tu.NewConst(0, NewQualVT(&Int32VT, K_QK_QNIL))
	c1 := tu.NewConst(1, NewQualVT(&Int32VT, K_QK_QNIL))
	label1 := EntityId(tu.GetUniqueLabelId())
	label2 := EntityId(tu.GetUniqueLabelId())

	// A block with all instructions.
	// It needs to be split into three basic blocks.
	bb := NewBasicBlock(tu.GetUniqueBBId(), 0, main.Id(), 2)
	tu.AddInsn(bb, AssignI(ValX(t1), BinX(K_XK_XLT, c0, argc)), nil)
	tu.AddInsn(bb, IfI(ValX(t1), BinX(K_XK_XVAL, label1, label2)), nil)
	tu.AddInsn(bb, LabelI(ValX(label1)), nil)
	tu.AddInsn(bb, ReturnI(ValX(c0)), nil)
	tu.AddInsn(bb, LabelI(ValX(label2)), nil)
	tu.AddInsn(bb, ReturnI(ValX(c1)), nil)
	main.body = bb // a single basic block is a Graph

	return tu
}

// This function creates a simple translation unit with a control flow graph.
// The program used is the same as in NewExampleTU_B_0.
// All instructions are in separate basic blocks here.
func NewExampleTU_B_1() *TU {
	tu := NewTU()

	main := tu.NewFunction("main", NewQualVT(&Int32VT, K_QK_QNIL), nil, nil)

	argc := tu.NewVar("argc", K_EK_EVAR_LOCL, NIL_ID, main.Id(), NewQualVT(&Int32VT, K_QK_QNIL))
	t1 := tu.NewVar("t1", K_EK_EVAR_LOCL_TMP, NIL_ID, main.Id(), NewQualVT(&Int32VT, K_QK_QNIL))
	c0 := tu.NewConst(0, NewQualVT(&Int32VT, K_QK_QNIL))
	c1 := tu.NewConst(1, NewQualVT(&Int32VT, K_QK_QNIL))

	// A block with all instructions.
	// It needs to be split into four basic blocks.
	ifbb := NewBasicBlock(tu.GetUniqueBBId(), 0, main.fid, 2)
	r0bb := NewBasicBlock(tu.GetUniqueBBId(), 0, main.fid, 2)
	r1bb := NewBasicBlock(tu.GetUniqueBBId(), 0, main.fid, 2)
	exit := NewBasicBlock(tu.GetUniqueBBId(), 0, main.fid, 2) // All CFGs have single exit block

	cfg := NewControlFlowGraph(tu, 0, main.fid)
	cfg.AddBBs(ifbb, r0bb, r1bb, exit)
	cfg.SetEntryBB(ifbb)
	cfg.SetExitBB(exit)

	ifbb.addSucc(r0bb).addSucc(r1bb)
	r0bb.addPred(ifbb).addSucc(exit)
	r1bb.addPred(ifbb).addSucc(exit)
	exit.addPred(r0bb).addPred(r1bb)

	tu.AddInsn(ifbb, AssignI(ValX(t1), BinX(K_XK_XLT, c0, argc)), nil)
	tu.AddInsn(ifbb, IfI(ValX(t1), BinX(K_XK_XVAL, EId(NIL_LABEL_ID), EId(NIL_LABEL_ID))), nil)
	tu.AddInsn(r0bb, ReturnI(ValX(c0)), nil)
	tu.AddInsn(r1bb, ReturnI(ValX(c1)), nil)
	tu.AddInsn(exit, NopI(), nil)

	main.body = cfg // a control flow graph is a Graph

	return tu
}
