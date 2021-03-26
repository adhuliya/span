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
      'ir.names.global': (None, {'g:0Null'}),
      'ir.var.real.count': 1, # the total vars in the translation unit
      'ir.var.abs.count': 2, # the total vars in the translation unit
      'ir.func.count': 2, # total functions (with or without body)
      'ir.func.def.count': 2, # total functions with definitions
      'ir.func.decl.count': 0, # total functions with declaration only
      'ir.record.count': 0, # total records (structs/unions)
    },

    "f:main": {
      'ir.cfg.node.count': 4, # the total nodes in the cfg
    }
  }
),

TestActionAndResult(
  action = "analyze",  # command line sub-command
  analysesExpr = "/+StrongLiveVarsA/",
  results = {
    "analysis.results": {
      "StrongLiveVarsA": {
        "f:main": { # data flow value at given node numbers
          2 : ("is: {'g:0Null'}", "is: bot"), # IN/OUT/False/True values
          3 : ("any", "is: {'g:0Null'}"), # IN/OUT/False/True values
        }
      }, # end analysis LiveVarsA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

TestActionAndResult(
  action = "analyze",  # command line sub-command
  analysesExpr = "/+IntervalA/",
  results = {
    "analysis.results": {
      "IntervalA": {
        "f:main": { # data flow value at given node numbers
          2 : ("any", "has: {'v:main:x': (20,20)}"), # IN/OUT/False/True values
        }
      }, # end analysis LiveVarsA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult

TestActionAndResult(
  action = "analyze",  # command line sub-command
  analysesExpr = "/+PointsToA/",
  results = {
    "analysis.results": {
      "PointsToA": {
        "f:main": { # data flow value at given node numbers
            2 : ("is: bot", "is: bot"), # IN/OUT/False/True values
        }
      }, # end analysis LiveVarsA
    }, # end analysis.results
  } # end of results
), # end TestActionAndResult
]
# BLOCK END  : list of test actions and results

