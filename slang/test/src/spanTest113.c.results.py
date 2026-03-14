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
    "callgraph.edges.count": 4,
    "callgraph.nodes.count": 4,
  }
),

]
# BLOCK END  : list of test actions and results

