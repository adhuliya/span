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
    GLOBAL_INITS_FUNC_NAME: {
      'ir.cfg.node.count': 4, # the total nodes in the cfg
      'ir.cfg.bb.edge.count': 1, # the total edges in the cfg
      'ir.cfg.bb.edge.false.true.pair.count': 0, # the total false/true edges pair in the cfg
      'ir.cfg.bb.edge.uncond.count': 1, # the total true edges in the cfg
      'ir.cfg.bb.has.edges': {
        (START_BB_ID, END_BB_ID, UnCondEdge),
      },
      'ir.cfg.bb.insn.count': {
        START_BB_ID: 3,
      },
      'ir.cfg.insn.nop.count': 2,
      'ir.cfg.start.end.node.is.insn.nop': True,
    },

    "f:main": {
      'ir.cfg.node.count': 10, # the total nodes in the cfg
      'ir.cfg.bb.edge.count': 1, # the total edges in the cfg
      'ir.cfg.bb.edge.false.true.pair.count': 0, # the total false/true edges pair in the cfg
      'ir.cfg.bb.edge.uncond.count': 1, # the total true edges in the cfg
      'ir.cfg.bb.has.edges': {
        (START_BB_ID, END_BB_ID, UnCondEdge),
      },
      'ir.cfg.bb.insn.count': {
        START_BB_ID: 9,
      },
      'ir.cfg.insn.nop.count': 2,
      'ir.cfg.start.end.node.is.insn.nop': True,
    }
  }
),

]
# BLOCK END  : list of test actions and results

