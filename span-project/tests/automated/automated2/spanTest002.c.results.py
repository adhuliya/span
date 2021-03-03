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

# BLOCK START: list of test actions and results
[

TestActionAndResult(
  action = "ir.checks",
  results = {
    'tunit': {
      'ir.var.count': 3, # the total vars in the translation unit
      'ir.func.count': 2, # total functions (with or without body)
      'ir.func.def.count': 2, # total functions with definitions
      'ir.func.decl.count': 0, # total functions with declaration only
      'ir.record.count': 0, # total functions with declaration only
    },

    'f:main': {
      'ir.cfg.node.count': 6, # the total nodes in the cfg
    }
  }
),

]
# BLOCK END  : list of test actions and results

