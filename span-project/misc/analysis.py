# BOUND START: regular_insn__other

def Num_Assign_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
    calleeBi: Opt[DfvPairL] = None,  #IPA
) -> DfvPairL:
  """Instr_Form: numeric: lhs = rhs.
  Convention:
    Type of lhs and rhs is numeric.
  """
  memberFuncName = instr.getFormalInstrStr(insn)
  f = getattr(self, memberFuncName)
  if instr.getCallExpr(insn):
    return f(nodeId, insn, nodeDfv, calleeBi)
  else:
    return f(nodeId, insn, nodeDfv)


def Ptr_Assign_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
    calleeBi: Opt[DfvPairL] = None,  #IPA
) -> DfvPairL:
  """Instr_Form: pointer: lhs = rhs.
  Convention:
    Type of lhs and rhs is a record.
  """
  memberFuncName = instr.getFormalInstrStr(insn)
  f = getattr(self, memberFuncName)
  if instr.getCallExpr(insn):
    return f(nodeId, insn, nodeDfv, calleeBi)
  else:
    return f(nodeId, insn, nodeDfv)


def Record_Assign_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
    calleeBi: Opt[DfvPairL] = None,  #IPA
) -> DfvPairL:
  """Instr_Form: record: lhs = rhs.
  Convention:
    Type of lhs and rhs is a record.
  """
  memberFuncName = instr.getFormalInstrStr(insn)
  f = getattr(self, memberFuncName)
  if instr.getCallExpr(insn):
    return f(nodeId, insn, nodeDfv, calleeBi)
  else:
    return f(nodeId, insn, nodeDfv)


def Num_Assign_Var_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: a = b.
  Convention:
    a and b are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = v.
  Convention:
    u and v are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_FuncName_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = f.
  Convention:
    u is a variable.
    f is a function name.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Var_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record(struct/union): a = b.
  Convention:
    a and b are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: a = b.
  Convention:
    a is a variable.
    b is a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: a = b.
  Convention:
    a is a variable.
    b is a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_SizeOf_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: a = sizeof(b).
  Convention:
    a and b are both variables.
    b is of type: types.VarArray only.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_UnaryArith_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: a = <unary arith/bit/logical op> b.
  Convention:
    a and b are both variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_BinArith_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: a = b <binary arith/rel/bit/shift> c.
  Convention:
    a is a variable.
    b, c: at least one of them is a variable.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_BinArith_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: a = b <binary +/-> c.
  Convention:
    a is a variable.
    b, c: at least one of them is a variable.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_Deref_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: a = *u.
  Convention:
    a and u are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_Deref_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = *v.
  Convention:
    u and v are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Var_Deref_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record: u = *v.
  Convention:
    v and u are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_Array_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: a = b[i].
  Convention:
    a and b are variables.
    i is a variable or a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_Array_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: u = a[i].
  Convention:
    u and a are variables.
    i is a variable or a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Var_Array_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record(struct/union): r = a[i].
  Convention:
    u and a are variables.
    i is a variable or a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_Member_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: a = b.x or a = b->x.
  Convention:
    a and b are variables.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_Member_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: a = b.x or a = b->x.
  Convention:
    a and b are variables.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Var_Member_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record(struct/union): a = b.x or a = b->x.
  Convention:
    a and b are variables.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_Select_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: b = c ? d : e.
  Convention:
    b, c, are always variables.
    d, e are variables or literals.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_Select_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: p = c ? d : e.
  Convention:
    b, c, are always variables.
    d, e are variables or literals.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Var_Select_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record: b = c ? d : e.
  Convention:
    b, c, d, e are always variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_Call_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
    calleeBi: Opt[DfvPairL] = None,  #IPA
) -> DfvPairL:
  """Instr_Form: numeric: b = func(args...).
  Convention:
    b is a variable.
    func is a function pointer or a function name.
    args are either a variable, a literal or addrof expression.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_Call_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
    calleeBi: Opt[DfvPairL] = None,  #IPA
) -> DfvPairL:
  """Instr_Form: pointer: p = func()."""
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Var_Call_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
    calleeBi: Opt[DfvPairL] = None,  #IPA
) -> DfvPairL:
  """Instr_Form: record: r = func()."""
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Var_CastVar_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: a = (int) b.
  Convention:
    a and b are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_CastVar_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: a = (int*) b.
  Convention:
    a and b are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_CastArr_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: b = (int*)a[i].
  Convention:
    b and a are variables.
    i is either a variable or a literal.
  Note:
    This instruction was necessary for expressions like,
      x = &a[0][1][2]; // where (say) x is int* and a is a[4][4][4].
    It is broken down as:
      t1 = (ptr to array of [4]) a[0];
      t2 = (ptr to int) t1[1];
      t3 = &t2[2];
      x = t3;
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


# Ptr_Assign_Var_CastMember_Instr() is not part of IR.
# its broken into: t1 = x.y; b = (int*) t1;

def Ptr_Assign_Var_AddrOfVar_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = &x.
  Convention:
    u and x are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_AddrOfArray_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = &a[i]
  Convention:
    u and a are variables.
    i is a variable of a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_AddrOfMember_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = &r.x or u = &r->x.
  Convention:
    u and r are variables.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_AddrOfDeref_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = &*x
  Convention:
    u is a pointer variable
    x is a pointer variable
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Var_AddrOfFunc_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: u = &f.
  Convention:
    u is a variable.
    f is function name.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


# BOUND END  : regular_insn__when_lhs_is_var
# BOUND START: regular_insn__when_lhs_is_deref

def Num_Assign_Deref_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: *u = b.
  Convention:
    u and b are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Deref_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: numeric: *u = b.
  Convention:
    u is a variable.
    b is a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Deref_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: *u = v.
  Convention:
    u and v are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Deref_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL
) -> DfvPairL:
  """Instr_Form: pointer: *u = b.
  Convention:
    u is a variable.
    b is a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Deref_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record: *u = v.
  Convention:
    u and v are variables.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


# BOUND END  : regular_insn__when_lhs_is_deref
# BOUND START: regular_insn__when_lhs_is_array

def Num_Assign_Array_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: a[i] = b.
  Convention:
    a and b are variables.
    i is either a variable or a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Array_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: a[i] = b.
  Convention:
    a is a variable.
    i is either a variable or a literal.
    b is a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Array_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: a[i] = b.
  Convention:
    a and b are variables.
    i is a variable or a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Array_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: a[i] = b.
  Convention:
    a is a variable.
    i is a variable or a literal.
    b is a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Array_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record(struct/union): a[i] = b.
  Convention:
    a and b are variables.
    i is a variable or a literal.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


# BOUND END  : regular_insn__when_lhs_is_array
# BOUND START: regular_insn__when_lhs_is_member_expr

def Num_Assign_Member_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: r.x = b  or r->x = b.
  Convention:
    r is a variable.
    b is a variable.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Num_Assign_Member_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: numeric: r.x = b or r->x = b.
  Convention:
    r is a variable.
    b is a literal.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Member_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: r.x = b  or r->x = b.
  Convention:
    r is a variable.
    b is a variable.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Ptr_Assign_Member_Lit_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: pointer: r.x = b or r->x = b.
  Convention:
    r is a variable.
    b is a literal.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


def Record_Assign_Member_Var_Instr(self,
    nodeId: NodeIdT,
    insn: instr.AssignI,
    nodeDfv: DfvPairL,
) -> DfvPairL:
  """Instr_Form: record(struct/union): r.x = b or r->x = b.
  Convention:
    r and b are variables.
    x is a member/field of a record.
  """
  return self.Default_Instr(nodeId, insn, nodeDfv)


# BOUND END  : regular_insn__when_lhs_is_member_expr
