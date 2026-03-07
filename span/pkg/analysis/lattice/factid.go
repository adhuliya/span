package lattice

// FactId uniquely identifies a data flow fact and its history of values.
// The 64 bits are encoded as follows:
//   - Most significant 3 bits are for future use
//   - Most significant 12 bits represent the analysis id.
//   - Next 37 bits (split like (4,8,25)) represents a unique id.
//     25 bits can be the id of the instruction/ basic block (BB) / function.
//     And the (4 + 8) bits can store if the id is for BB/function,
//     or its at the start, end or inside of the BB/function.
//   - Next 12 bits represents the version of the fact (every update shall increment the version part)
//
// The FactId can be used as key by dropping the 'version' part.
// It may be used as key with the 'version' part if it needs to be so detailed.
type FactId = uint64

// Type of the data flow fact
// 0b000 - entry of an instruction
// 0b001 - exit of an instruction
// 0b010 - entry of the function
// 0b011 - exit of the function (all functions have single exit)
// 0b100 - entry of the BB
// 0b101 - entry of an instruction in BB
// 0b110 - exit of the an instruction in BB (sequence number of instruction in 8 bits)
// 0b111 - exit of the BB (sequence number of instruction in 8 bits)
