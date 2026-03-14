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
    "tunit": {
      'ir.names.global': (None, {'g:0Null', 'g:a', 'g:b'}),
      'ir.var.real.count': 2, # the total vars in the translation unit
      'ir.var.abs.count': 2, # the total vars in the translation unit
      'ir.func.count': 3, # total functions (with or without body)
      'ir.func.def.count': 3, # total functions with definitions
      'ir.func.decl.count': 0, # total functions with declaration only
      'ir.record.count': 0, # total records (structs/unions)
    },

    "f:main": {
      'ir.cfg.node.count': 5, # the total nodes in the cfg
    }
  }
),

TestActionAndResult(
  action = "ipa",  # command line sub-command
  analysesExpr = "/+IntervalA/",
  results = {
    "analysis.results": {
      "IntervalA": {
        "f:main": { # data flow value at given node numbers
          3 : ("any", "has: {'g:a': (30,30), 'g:b': (40,40)}"), # IN/OUT/False/True values
        }
      }, # end analysis LiveVarsA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

]
# BLOCK END  : list of test actions and results

