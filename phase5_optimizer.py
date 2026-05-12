"""
PHASE 5 — CODE OPTIMIZATION
Applies constant folding and constant propagation to the TAC.
  - Constant folding  : e.g.  t1 = 5 + 10  →  t1 = 15
  - Constant propagation : e.g.  x = 5  then  t2 = x + 1  →  t2 = 6
Run standalone: python phase5_optimizer.py
"""

import re
import operator
from phase4_irgen import generate_ir

_ARITH_OPS = {'+': operator.add, '-': operator.sub,
              '*': operator.mul, '/': operator.floordiv}
_REL_OPS   = {'<': operator.lt,  '>': operator.gt,
              '<=': operator.le, '>=': operator.ge,
              '==': operator.eq, '!=': operator.ne}


def optimize(ir_code):
    """
    Single-pass constant folding + propagation.
    Returns new list of (possibly annotated) instruction strings.
    """
    constants = {}   # name → known int value
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
        # ── t = a arith b ────────────────────────────────────
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

        # ── t = a relop b ─────────────────────────────────────
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

        # ── x = val  (simple copy / constant load) ───────────
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

        # ── everything else (labels, jumps, prints) ──────────
        optimized.append(instr)

    return optimized


def optimize_from_source(source):
    """Full pipeline: source → TAC → optimized TAC."""
    ir_code = generate_ir(source)
    return ir_code, optimize(ir_code)


# ── Standalone runner ─────────────────────────────────────────

SAMPLE_SOURCE = """\
int x = 5;
int y = 10;
int z = x + y;
if (z > 10) {
    print(z);
} else {
    print(x);
}
while (x < 3) {
    x = x + 1;
    print(x);
}
"""

if __name__ == '__main__':
    print('=' * 50)
    print('  PHASE 5 — Code Optimization')
    print('=' * 50)
    ir_code, opt_ir = optimize_from_source(SAMPLE_SOURCE)

    print('\n  Before optimization (TAC):')
    for line in ir_code:
        print(f'    {line}')

    print('\n  After optimization:')
    for line in opt_ir:
        print(f'    {line}')

    folded = sum(1 for l in opt_ir if '; folded' in l)
    prop   = sum(1 for l in opt_ir if '; propagated' in l)
    print(f'\n  Optimizations applied: {folded} folds, {prop} propagations')
