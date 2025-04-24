package spir

// This file defines the SPAN IR context object.
// The context object is used to store the state of the SPAN IR.
// It maintains the necessary state information for the underlying TranslationUnit.

type Context struct {
	translationUnit *TranslationUnit
	info            map[uint32]any
}

func NewContext(tu *TranslationUnit) *Context {
	return &Context{
		translationUnit: tu,
		info:            make(map[uint32]any),
	}
}

func (c *Context) TranslationUnit() *TranslationUnit {
	return c.translationUnit
}

func (c *Context) SetInfo(key uint32, value any) bool {
	if _, ok := c.info[key]; ok {
		return false
	}
	// Set the value in the context info map.
	c.info[key] = value
	return true
}

func (c *Context) GetInfo(key uint32) (any, bool) {
	value, ok := c.info[key]
	return value, ok
}

func (c *Context) RemoveInfo(key uint32) bool {
	if _, ok := c.info[key]; !ok {
		return false
	}
	delete(c.info, key)
	return true
}
