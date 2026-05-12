"""
PHASE 6 — CODE GENERATION
Translates optimized TAC into stack-based pseudo-assembly.
"""

import re
from .phase5_optimizer import optimize_from_source

_ARITH_INST = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV'}
_REL_INST   = {'<': 'CLT', '>': 'CGT', '<=': 'CLE',
               '>=': 'CGE', '==': 'CEQ', '!=': 'CNE'}


def code_gen(optimized_ir):
    """Translate optimized TAC list → pseudo-assembly lines."""
    asm = ['; ===== Generated Pseudo-Assembly =====', '']

    declared = set()
    for instr in optimized_ir:
        m = re.match(r'^(\w+) = ', instr)
        if m:
            name = m.group(1)
            if not re.match(r'^t\d+$', name):
                declared.add(name)

    asm.append('.data')
    for v in sorted(declared):
        asm.append(f'    {v:<8} DW  0')
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

        m = re.match(r'^print (\w+)$', instr)
        if m:
            asm.append(f'    PUSH  {m.group(1)}')
            asm.append(f'    CALL  print')
            continue

        m = re.match(r'^ifFalse (\w+) goto (\w+)$', instr)
        if m:
            asm.append(f'    LOAD  {m.group(1)}')
            asm.append(f'    JZ    {m.group(2)}')
            continue

        m = re.match(r'^goto (\w+)$', instr)
        if m:
            asm.append(f'    JMP   {m.group(1)}')
            continue

        m = re.match(r'^(\w+) = (\w+) ([+\-*/]) (\w+)$', instr)
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
