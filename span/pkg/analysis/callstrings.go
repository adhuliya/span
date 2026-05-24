package analysis

import (
	"fmt"

	"github.com/adhuliya/span/pkg/analysis/lattice"
	"github.com/adhuliya/span/pkg/spir"
)

const CALL_STR_ARR_LEN = 4

type CallString struct {
	klimit     int                               // The limit on the length of the call strings (max 3)
	callString [CALL_STR_ARR_LEN]spir.FuncId     // The call string -- sequence of function calls
	callSites  [CALL_STR_ARR_LEN]spir.CallSiteId // The call sites involved in the call string
}

// CreateCallString constructs a CallString using the topmost elements of the
// function call stack and call site stack according to the klimit.
// - funcStack: stack holding function IDs (FuncId)
// - callsiteStack: stack holding call site IDs (CallSiteId)
// - klimit: maximum number of context elements to track
func CreateCallString(funcStack, callsiteStack *spir.EntityStack, klimit int) CallString {
	// Ensure we do not exceed CALL_STR_ARR_LEN or klimit
	if klimit > CALL_STR_ARR_LEN {
		klimit = CALL_STR_ARR_LEN
	}

	cs := CallString{}
	cs.klimit = klimit
	// Convert each [4]EntityId value from the stack to the correct type (FuncId, CallSiteId)
	{
		peekFuncIds := funcStack.Peek4()
		for i := 0; i < cs.klimit && i < len(peekFuncIds); i++ {
			cs.callString[i] = spir.FuncId(peekFuncIds[i])
		}
		peekCallSiteIds := callsiteStack.Peek4()
		for i := 0; i < cs.klimit && i < len(peekCallSiteIds); i++ {
			cs.callSites[i] = spir.CallSiteId(peekCallSiteIds[i])
		}
	}
	return cs
}

func (cs *CallString) String() string {
	return fmt.Sprintf("CallString(callString=%v, callSites=%v)", cs.callString, cs.callSites)
}

type CallStringsInfo struct {
	klimit int           // The limit on the length of the call strings (max 3)
	ctx    *spir.Context // The context for the analysis

	callSiteStack *spir.EntityStack // The stack of call sites
	funcCallStack *spir.EntityStack // The stack of function calls

	callSiteFactMap     InsnFactMap                     // The fact map for the call site
	callSiteToInsnIdMap map[spir.CallSiteId]spir.InsnId // The map of call site to instruction id

	// Contains the context information of functions for each call string
	boundaryInfo map[CallString]lattice.Pair // The map of call string to boundary information
}
