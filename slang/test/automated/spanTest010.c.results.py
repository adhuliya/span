# a python dictionary with desired states in SPAN

# this files exptects necessary imports in the module eval()ing it.

# import span.ir.types as types
# import span.ir.op as op
# import span.ir.expr as expr
# import span.ir.instr as instr
# import span.ir.constructs as constructs
# import span.ir.tunit as tunit
# import span.ir.ir as ir
# import span.tests.testing as testing

# import span.clients.liveness as liveness

# BLOCK START: list of test actions and results
[

TestActionAndResult(
  action = "ir.checks",
  results = {
    "f:main": {
      'ir.cfg.node.count': 8, # the total nodes in the cfg
      'ir.cfg.bb.edge.count': 5, # the total edges in the cfg
      'ir.cfg.bb.edge.false.true.pair.count': 1, # the total false/true edges pair in the cfg
      'ir.cfg.bb.edge.uncond.count': 3, # the total true edges in the cfg
      'ir.cfg.bb.has.edges': {
        (START_BB_ID, 1, TrueEdge),
        (1, 2, UnCondEdge),
        (START_BB_ID, 2, FalseEdge),
        (4, END_BB_ID, UnCondEdge),
      },
      'ir.cfg.bb.insn.count': {
        START_BB_ID: 4,
      },
      'ir.cfg.insn.nop.count': 2,
      'ir.cfg.start.end.node.is.insn.nop': True,
    }
  }
),

]
# BLOCK END  : list of test actions and results

