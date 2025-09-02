package spir

// This file defines the SPAN IR context object.
// The context object is used to store the state of the SPAN IR.
// It maintains the necessary state information for the underlying TranslationUnit(s)

type ContextId uint32

var contextIdCounter ContextId = 0

func GetNextContextId() ContextId {
	contextIdCounter++
	return contextIdCounter
}

type Context struct {
	translationUnit *TU
	info            map[ContextId]any
}

func NewContext(tu *TU) *Context {
	return &Context{
		translationUnit: tu,
		info:            make(map[ContextId]any),
	}
}

func (c *Context) TU() *TU {
	return c.translationUnit
}

func (c *Context) SetInfo(key ContextId, value any) bool {
	if _, ok := c.info[key]; ok {
		return false
	}
	// Set the value in the context info map.
	c.info[key] = value
	return true
}

func (c *Context) GetInfo(key ContextId) (any, bool) {
	value, ok := c.info[key]
	return value, ok
}

func (c *Context) RemoveInfo(key ContextId) bool {
	if _, ok := c.info[key]; !ok {
		return false
	}
	delete(c.info, key)
	return true
}
