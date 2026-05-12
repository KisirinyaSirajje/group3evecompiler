"""
PHASE 5 — CODE OPTIMIZATION
Applies constant folding and constant propagation.
"""

import re
import operator
from .phase4_irgen import generate_ir

_ARITH_OPS = {'+': operator.add, '-': operator.sub,
              '*': operator.mul, '/': operator.floordiv}
_REL_OPS   = {'<': operator.lt,  '>': operator.gt,
              '<=': operator.le, '>=': operator.ge,
              '==': operator.eq, '!=': operator.ne}


def optimize(ir_code):
    """Single-pass constant folding + propagation."""
    constants = {}
    optimized = []

    def resolve(name):
        if name in constants:
            return constants[name]
        try:
            return int(name)
        except ValueError:
            return None

    def sub(name):
        v = resolve(name)
        return str(v) if v is not None else name

    for instr in ir_code:
        m = re.match(r'^(\w+) = (\w+) ([+\-*/]) (\w+)$', instr)
        if m:
            dest, left, op, right = m.groups()
            lv, rv = resolve(left), resolve(right)
            if lv is not None and rv is not None:
                result = _ARITH_OPS[op](lv, rv)
                constants[dest] = result
                optimized.append(f'{dest} = {result:<6}  ; folded: {left} {op} {right} = {result}')
            else:
                optimized.append(f'{dest} = {sub(left)} {op} {sub(right)}')
            continue

        m = re.match(r'^(\w+) = (\w+) ([<>]=?|==|!=) (\w+)$', instr)
        if m:
            dest, left, op, right = m.groups()
            lv, rv = resolve(left), resolve(right)
            if lv is not None and rv is not None:
                result = int(_REL_OPS[op](lv, rv))
                constants[dest] = result
                optimized.append(f'{dest} = {result:<6}  ; folded: {left} {op} {right} = {result}')
            else:
                optimized.append(f'{dest} = {sub(left)} {op} {sub(right)}')
            continue

        m = re.match(r'^(\w+) = (\w+)$', instr)
        if m:
            dest, src = m.groups()
            val = resolve(src)
            if val is not None:
                constants[dest] = val
                optimized.append(f'{dest} = {val:<6}  ; propagated')
            else:
                optimized.append(instr)
            continue

        optimized.append(instr)

    return optimized


def optimize_from_source(source):
    """Full pipeline: source → TAC → optimized TAC."""
    ir_code = generate_ir(source)
    return ir_code, optimize(ir_code)
