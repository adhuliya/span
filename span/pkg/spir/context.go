package spir

// This file defines the SPAN IR context object.
// The context object is used to store the state of the SPAN IR.
// It maintains the necessary state information for the underlying TranslationUnit(s).

type ContextId uint64

var contextIdCounter ContextId = 0

func GetNextContextId() ContextId {
	contextIdCounter++
	return contextIdCounter
}

type Context struct {
	tu   *TU
	info map[uint64]any // key is the instance id / context id
}

func NewContext(tu *TU) *Context {
	return &Context{
		tu:   tu,
		info: make(map[uint64]any),
	}
}

func (c *Context) TU() *TU {
	return c.tu
}

func (c *Context) SetInfo(key uint64, value any) bool {
	if _, ok := c.info[key]; ok {
		return false
	}
	// Set the value in the context info map.
	c.info[key] = value
	return true
}

func (c *Context) GetInfo(key uint64) (any, bool) {
	value, ok := c.info[key]
	return value, ok
}

func (c *Context) RemoveInfo(key uint64) bool {
	if _, ok := c.info[key]; !ok {
		return false
	}
	delete(c.info, key)
	return true
}
