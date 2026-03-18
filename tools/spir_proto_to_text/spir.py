#! /usr/bin/env python3

"""
This script takes a SPAN IR protobuf file as input and outputs a text file.
The text file is a human-readable representation of the SPAN IR.
In the future, this script can be used to query SPAN IR for different purposes.

It prints the following information:
1. All global variables and their types.
2. All the local variables and their types.
3. All named entities and their types:
   - Function names and their parameters, return type, and properties like variadic, etc.
   - Struct names and their fields and their types.
   - Union names and their fields and their types.
4. Function body with the sequence of instructions:
   - Print instructions with simple entity names (last part of the compound name) instead of the full compound name.
   - Entity names can be found in BitEntityInfo objects in the protobuf file.
   - Don't print type information when printing the instructions.
   - Keep one instruction per line.
   - Use indentation to keep track of the control flow.
"""

import argparse
import sys
import os

# Importing Google protobuf
try:
    import google.protobuf
    # You need to generate python bindings for spir.proto:
    # protoc --python_out=. span/pkg/spir/spir.proto
    import spir_pb2 as spir_pb2
except ImportError as e:
    print("Error: Could not import required modules. Make sure you have compiled the protobuf as python bindings.", file=sys.stderr)
    print(e, file=sys.stderr)
    sys.exit(1)

from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(
        description="Print human-readable text for a SPAN IR protobuf file."
    )
    parser.add_argument("input", help="SPAN IR proto file (BitTU) - binary or text")
    parser.add_argument("-o", "--output", help="Output text file (default: stdout)", default=None)
    parser.add_argument("--proto_text", action="store_true", help="Input is a text proto instead of binary")
    return parser.parse_args()

# Helper: last part of a compound entity name
def simple_name(name):
    return name.split(":")[-1] if ":" in name else name

# Helper: Find entity name and BitEntityInfo from eid
def find_entity_name_from_eid(bit_tu, eid):
    for name, idval in bit_tu.namesToIds.items():
        if idval == eid:
            return name
    return None

def get_bit_entity_info(bit_tu, eid):
    return bit_tu.entityInfo.get(eid, None)

def get_data_type(bit_tu, eid):
    return bit_tu.dataTypes.get(eid, None)

def print_globals(bit_tu, out):
    out.write("Globals:\n")
    for eid, einfo in bit_tu.entityInfo.items():
        if einfo.ekind == spir_pb2.K_EK.EVAR_GLBL:
            gname = find_entity_name_from_eid(bit_tu, eid)
            typename = ""
            if hasattr(einfo, "dataTypeEid"):
                tid = getattr(einfo, "dataTypeEid")
                dt = get_data_type(bit_tu, tid)
                typename = f": {format_type(bit_tu, dt)}" if dt else ""
            out.write(f"  {gname}{typename}\n")
    out.write("\n")

def format_type(bit_tu, dtype, depth=0):
    # Pretty print a BitDataType (recursive)
    if dtype is None:
        return "<?>"
    spir = spir_pb2  # shorcut
    vkind_name = spir_pb2.K_VK.Name(dtype.vkind) if dtype.HasField("vkind") else "Unknown"
    if dtype.vkind in (spir.K_VK.TINT32, spir.K_VK.TINT8, spir.K_VK.TINT16, spir.K_VK.TINT64,
                       spir.K_VK.TUINT32, spir.K_VK.TUINT8, spir.K_VK.TUINT16, spir.K_VK.TUINT64, 
                       spir.K_VK.TFLOAT32, spir.K_VK.TFLOAT64, spir.K_VK.TVOID):
        return vkind_name.replace("T", "")
    if dtype.vkind in (spir.K_VK.TARR_FIXED, spir.K_VK.TARR_VARIABLE, spir.K_VK.TARR_PARTIAL):
        elem_dt = get_data_type(bit_tu, dtype.subTypeEid)
        return f"{format_type(bit_tu, elem_dt)}[{dtype.len if dtype.HasField('len') else '?'}]"
    if dtype.vkind == spir.K_VK.TSTRUCT or dtype.vkind == spir.K_VK.TUNION:
        name = dtype.typeName if dtype.HasField("typeName") else vkind_name
        return name
    if dtype.vkind == spir.K_VK.TPTR_TO_VOID:
        return "void*"
    if dtype.vkind in (spir.K_VK.TPTR_TO_CHAR, spir.K_VK.TPTR_TO_INT, spir.K_VK.TPTR_TO_FLOAT, spir.K_VK.TPTR_TO_RECORD):
        base_dt = get_data_type(bit_tu, dtype.subTypeEid)
        return f"{format_type(bit_tu, base_dt)}*"
    if dtype.vkind == spir.K_VK.TPTR_TO_FUNC:
        base_dt = get_data_type(bit_tu, dtype.subTypeEid)
        return f"(*func)({format_type(bit_tu, base_dt)})"
    return vkind_name

def print_structs_and_unions(bit_tu, out):
    structs = []
    unions = []
    for eid, dt in bit_tu.dataTypes.items():
        if dt.vkind == spir_pb2.K_VK.TSTRUCT:
            structs.append((eid, dt))
        elif dt.vkind == spir_pb2.K_VK.TUNION:
            unions.append((eid, dt))

    out.write("Structs:\n")
    for eid, dt in structs:
        out.write(f"  {dt.typeName if dt.HasField('typeName') else f'struct_{eid}'}:\n")
        for idx, (fid, ftypeid) in enumerate(zip(dt.fopIds, dt.fopTypeEids)):
            field_dt = get_data_type(bit_tu, ftypeid)
            field_name = find_entity_name_from_eid(bit_tu, fid)
            out.write(f"    {field_name if field_name else f'field_{fid}'}: {format_type(bit_tu, field_dt)}\n")
        out.write("\n")
    out.write("Unions:\n")
    for eid, dt in unions:
        out.write(f"  {dt.typeName if dt.HasField('typeName') else f'union_{eid}'}:\n")
        for idx, (fid, ftypeid) in enumerate(zip(dt.fopIds, dt.fopTypeEids)):
            field_dt = get_data_type(bit_tu, ftypeid)
            field_name = find_entity_name_from_eid(bit_tu, fid)
            out.write(f"    {field_name if field_name else f'field_{fid}'}: {format_type(bit_tu, field_dt)}\n")
        out.write("\n")

def print_functions(bit_tu, out):
    out.write("Functions:\n")
    for func in bit_tu.functions:
        fname = func.fname
        finfo = get_bit_entity_info(bit_tu, func.fid)
        out.write(f"  {fname}(")
        # function parameters and their types
        params = []
        if finfo and hasattr(finfo, 'dataTypeEid'):
            f_dt = get_data_type(bit_tu, finfo.dataTypeEid)
            if f_dt and hasattr(f_dt, 'fopIds') and hasattr(f_dt, 'fopTypeEids'):
                for pid, ptypeid in zip(f_dt.fopIds, f_dt.fopTypeEids):
                    param_name = find_entity_name_from_eid(bit_tu, pid)
                    param_type = format_type(bit_tu, get_data_type(bit_tu, ptypeid))
                    params.append(f"{param_name if param_name else 'p'+str(pid)}: {param_type}")
        out.write(", ".join(params))
        out.write(")")
        # function return type
        if finfo and hasattr(finfo, 'dataTypeEid'):
            f_dt = get_data_type(bit_tu, finfo.dataTypeEid)
            if f_dt and f_dt.HasField('subTypeEid'):
                ret_dt = get_data_type(bit_tu, f_dt.subTypeEid)
                out.write(f" -> {format_type(bit_tu, ret_dt)}")
        if func.is_variadic:
            out.write(" [variadic]")
        out.write("\n")
    out.write("\n")

def print_locals_vars_in_funcs(bit_tu, out):
    for func in bit_tu.functions:
        fname = func.fname
        out.write(f"Locals in {fname}:\n")
        # Find locals by scanning entityInfo for locals with parentEid == func.fid
        for eid, einfo in bit_tu.entityInfo.items():
            if einfo.ekind == spir_pb2.K_EK.EVAR_LOCL and getattr(einfo, "parentEid", None) == func.fid:
                vname = find_entity_name_from_eid(bit_tu, eid)
                vtype = ""
                if hasattr(einfo, "dataTypeEid"):
                    v_dt = get_data_type(bit_tu, einfo.dataTypeEid)
                    vtype = f": {format_type(bit_tu, v_dt)}" if v_dt else ""
                out.write(f"  {vname}{vtype}\n")
        out.write("\n")

def print_function_bodies(bit_tu, out):
    for func in bit_tu.functions:
        out.write(f"Function {func.fname} body:\n")
        print_instructions(func, bit_tu, out, indent=2)
        out.write("\n")

def print_instructions(func, bit_tu, out, indent=2):
    # Indentation and simple instruction print
    for insn in func.insns:
        line = " " * indent
        kinstr = spir_pb2.K_IK.Name(insn.ikind)
        parts = [kinstr]
        # Print only the simple form for instructions
        if insn.HasField('expr1'):
            parts.append(display_expr(insn.expr1, bit_tu))
        if insn.HasField('expr2'):
            parts.append(display_expr(insn.expr2, bit_tu))
        out.write(line + " ".join(parts) + "\n")

def literal_to_string(einfo):
    """
    Returns a string representation of the literal value from BitEntityInfo,
    reading its lowVal, highVal, or strVal fields depending on ekind.
    """
    if not einfo or not hasattr(einfo, "ekind"):
        return "(unhandled-literal)"

    if einfo.ekind == spir_pb2.K_EK.ELIT_NUM or einfo.ekind == spir_pb2.K_EK.ELIT_NUM_IMM:
        vals = []
        if hasattr(einfo, "lowVal"):
            vals.append(str(einfo.lowVal))
        if hasattr(einfo, "highVal") and einfo.highVal != 0:
            vals.append(str(einfo.highVal))
        return ":".join(vals) if vals else "0"
    if einfo.ekind == spir_pb2.K_EK.ELIT_STR:
        value = getattr(einfo, "strVal", "")
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return f'"{value}"'
    # You may define ELIT_FLOAT/ELIT_BOOL as needed
    if einfo.ekind == spir_pb2.K_EK.ELIT_BOOL:
        return "true" if getattr(einfo, "lowVal", 0) else "false"
    return "(unhandled-literal)"

def find_entity_name_from_eid(bit_tu, eid):
    """
    Finds and returns the entity name for a given entity id.
    If the entity is a literal (ELIT_*), returns its literal representation.
    """
    if not eid:
        return ""
    einfo = bit_tu.entityInfo.get(eid, None)
    # Check for literal entity kinds and use literal_to_string
    if einfo is not None and hasattr(einfo, "ekind") and (
        einfo.ekind in (
            getattr(spir_pb2.K_EK, 'ELIT_NUM', -1),
            getattr(spir_pb2.K_EK, 'ELIT_NUM_IMM', -1),
            getattr(spir_pb2.K_EK, 'ELIT_STR', -1),
            getattr(spir_pb2.K_EK, 'ELIT_BOOL', -1)
        )
    ):
        return literal_to_string(einfo)
    # Otherwise, look up the name
    for name, id_ in getattr(bit_tu, "namesToIds", {}).items():
        if id_ == eid:
            return name
    return ""

def display_expr(expr, bit_tu):
    """
    Print simple entity names or the literal value if present.
    Uses find_entity_name_from_eid, which internally handles literals.
    """
    kxkind = spir_pb2.K_XK.Name(expr.xkind)
    if expr.xkind == spir_pb2.K_XK.XVAL:
        # Use oprnd1eid to look up entity info or literal
        if expr.HasField("oprnd1eid"):
            eid = expr.oprnd1eid
            nm = find_entity_name_from_eid(bit_tu, eid)
            return simple_name(nm) if nm else f"id:{eid}"
        return "(imm?)"
    elif expr.xkind in [
        spir_pb2.K_XK.XADD, spir_pb2.K_XK.XSUB, spir_pb2.K_XK.XMUL, spir_pb2.K_XK.XDIV,
        spir_pb2.K_XK.XMOD, spir_pb2.K_XK.XAND, spir_pb2.K_XK.XOR, spir_pb2.K_XK.XXOR,
        spir_pb2.K_XK.XSHL, spir_pb2.K_XK.XSHR, spir_pb2.K_XK.XEQ, spir_pb2.K_XK.XNE,
        spir_pb2.K_XK.XLT, spir_pb2.K_XK.XGE
    ]:
        def operand_to_str(operand_eid):
            if operand_eid == 0:
                return ""
            nm = find_entity_name_from_eid(bit_tu, operand_eid)
            return simple_name(nm) if nm else f"id:{operand_eid}"
        op1 = operand_to_str(expr.oprnd1eid) if expr.HasField("oprnd1eid") else ""
        op2 = operand_to_str(expr.oprnd2eid) if expr.HasField("oprnd2eid") else ""
        return f"{kxkind}({op1}, {op2})"
    elif expr.xkind == spir_pb2.K_XK.XCALL:
        args = [simple_name(find_entity_name_from_eid(bit_tu, eid)) for eid in expr.oprnds]
        return f"call({', '.join(args)})"
    else:
        ops = []
        if expr.HasField("oprnd1eid"):
            eid = expr.oprnd1eid
            nm1 = find_entity_name_from_eid(bit_tu, eid)
            ops.append(simple_name(nm1) if nm1 else f"id:{eid}")
        if expr.HasField("oprnd2eid"):
            eid = expr.oprnd2eid
            nm2 = find_entity_name_from_eid(bit_tu, eid)
            ops.append(simple_name(nm2) if nm2 else f"id:{eid}")
        if expr.oprnds:
            for eid in expr.oprnds:
                nm = find_entity_name_from_eid(bit_tu, eid)
                ops.append(simple_name(nm) if nm else f"id:{eid}")
        return f"{kxkind}({', '.join(ops)})" if ops else kxkind

def main():
    args = parse_args()
    # Read the proto
    with open(args.input, "rb" if not args.proto_text else "r") as f:
        bit_tu = spir_pb2.BitTU()
        if args.proto_text:
            import google.protobuf.text_format
            google.protobuf.text_format.Merge(f.read(), bit_tu)
        else:
            bit_tu.ParseFromString(f.read())

    out = open(args.output, "w") if args.output else sys.stdout

    print_globals(bit_tu, out)
    print_structs_and_unions(bit_tu, out)
    print_functions(bit_tu, out)
    print_locals_vars_in_funcs(bit_tu, out)
    print_function_bodies(bit_tu, out)

    if args.output:
        out.close()

if __name__ == "__main__":
    main()
