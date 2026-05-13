"""
PHASE 6 — CODE GENERATION
Translates optimized TAC into stack-based pseudo-assembly.
"""

import re
from .phase5_optimizer import optimize_from_source

_ARITH_INST = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD'}
_REL_INST   = {'<': 'CLT', '>': 'CGT', '<=': 'CLE',
               '>=': 'CGE', '==': 'CEQ', '!=': 'CNE'}


def code_gen(optimized_ir):
    """Translate optimized TAC list → pseudo-assembly lines."""
    asm = ['; ===== Generated Pseudo-Assembly =====', '']

    declared = set()
    arrays   = {}
    for instr in optimized_ir:
        m = re.match(r'^(\w+) = ', instr)
        if m:
            name = m.group(1)
            if not re.match(r'^t\d+$', name):
                declared.add(name)
        m = re.match(r'^array (\w+)\[(\w+)\]$', instr)
        if m:
            arrays[m.group(1)] = m.group(2)
            declared.discard(m.group(1))

    asm.append('.data')
    for v in sorted(declared):
        asm.append(f'    {v:<8} DW  0')
    for name, size in sorted(arrays.items()):
        asm.append(f'    {name:<8} DW  0[{size}]')
    asm.append('')
    asm.append('.code')

    def clean(instr):
        return instr.split(';')[0].strip()

    for raw in optimized_ir:
        instr = clean(raw)
        if not instr:
            continue

        if re.match(r'^\w+:$', instr):
            asm.append(f'{instr}')
            continue

        m = re.match(r'^func_begin (\w+)$', instr)
        if m:
            asm.append(f'')
            asm.append(f'{m.group(1)}:')
            continue

        m = re.match(r'^func_end \w+$', instr)
        if m:
            asm.append(f'    RET')
            continue

        m = re.match(r'^param (\w+)$', instr)
        if m:
            asm.append(f'    ; param {m.group(1)}')
            continue

        m = re.match(r'^return(?: (.+))?$', instr)
        if m:
            val = m.group(1)
            if val:
                asm.append(f'    LOAD  {val}')
            asm.append(f'    RET')
            continue

        m = re.match(r'^read (\w+)$', instr)
        if m:
            asm.append(f'    CALL  input')
            asm.append(f'    STORE {m.group(1)}')
            continue

        m = re.match(r'^push_arg (\S+)$', instr)
        if m:
            asm.append(f'    PUSH  {m.group(1)}')
            continue

        m = re.match(r'^(\w+) = call (\w+)$', instr)
        if m:
            asm.append(f'    CALL  {m.group(2)}')
            asm.append(f'    STORE {m.group(1)}')
            continue

        m = re.match(r'^call (\w+)$', instr)
        if m:
            asm.append(f'    CALL  {m.group(1)}')
            continue

        m = re.match(r'^array \w+\[\w+\]$', instr)
        if m:
            continue  # handled in .data section

        m = re.match(r'^print (.+)$', instr)
        if m:
            asm.append(f'    PUSH  {m.group(1)}')
            asm.append(f'    CALL  print')
            continue

        m = re.match(r'^ifFalse (\w+) goto (\w+)$', instr)
        if m:
            asm.append(f'    LOAD  {m.group(1)}')
            asm.append(f'    JZ    {m.group(2)}')
            continue

        m = re.match(r'^ifTrue (\w+) goto (\w+)$', instr)
        if m:
            asm.append(f'    LOAD  {m.group(1)}')
            asm.append(f'    JNZ   {m.group(2)}')
            continue

        m = re.match(r'^goto (\w+)$', instr)
        if m:
            asm.append(f'    JMP   {m.group(1)}')
            continue

        m = re.match(r'^(\w+) = (\w+) ([+\-*/%]) (\w+)$', instr)
        if m:
            dest, left, op, right = m.groups()
            asm.append(f'    LOAD  {left}')
            asm.append(f'    {_ARITH_INST[op]:<5} {right}')
            asm.append(f'    STORE {dest}')
            continue

        m = re.match(r'^(\w+) = (\w+) ([<>]=?|==|!=) (\w+)$', instr)
        if m:
            dest, left, op, right = m.groups()
            asm.append(f'    LOAD  {left}')
            asm.append(f'    {_REL_INST[op]:<5} {right}')
            asm.append(f'    STORE {dest}')
            continue

        m = re.match(r'^(\w+) = (\w+) (&&|\|\|) (\w+)$', instr)
        if m:
            dest, left, op, right = m.groups()
            inst = 'AND' if op == '&&' else 'OR'
            asm.append(f'    LOAD  {left}')
            asm.append(f'    {inst:<5} {right}')
            asm.append(f'    STORE {dest}')
            continue

        m = re.match(r'^(\w+) = ! (\w+)$', instr)
        if m:
            asm.append(f'    LOAD  {m.group(2)}')
            asm.append(f'    NOT')
            asm.append(f'    STORE {m.group(1)}')
            continue

        m = re.match(r'^(\w+)\[(\w+)\] = (\w+)$', instr)
        if m:
            name, idx, val = m.groups()
            asm.append(f'    LOAD  {val}')
            asm.append(f'    STOREI {name}[{idx}]')
            continue

        m = re.match(r'^(\w+) = (\w+)\[(\w+)\]$', instr)
        if m:
            dest, name, idx = m.groups()
            asm.append(f'    LOADI {name}[{idx}]')
            asm.append(f'    STORE {dest}')
            continue

        m = re.match(r'^(\w+) = (\S+)$', instr)
        if m:
            dest, src = m.groups()
            asm.append(f'    LOAD  {src}')
            asm.append(f'    STORE {dest}')
            continue

    asm.append('    HALT')
    return asm


def compile_to_asm(source):
    """Full pipeline: source → optimized TAC → assembly."""
    ir_code, opt_ir = optimize_from_source(source)
    return opt_ir, code_gen(opt_ir)
