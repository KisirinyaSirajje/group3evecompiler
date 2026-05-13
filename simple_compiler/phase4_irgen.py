"""
PHASE 4 — INTERMEDIATE CODE GENERATION
Converts the AST into Three-Address Code (TAC) using temporaries (t1, t2…)
and labels (L1, L2…) for control flow.
Run standalone: python phase4_irgen.py
"""

from simple_compiler.phase3_semantic import analyze


class IRGenerator:
    def __init__(self):
        self.code       = []
        self._tmp_count = 0
        self._lbl_count = 0

    def _tmp(self):
        self._tmp_count += 1
        return f't{self._tmp_count}'

    def _lbl(self):
        self._lbl_count += 1
        return f'L{self._lbl_count}'

    def _emit(self, instr):
        self.code.append(instr)

    def generate(self, node):
        kind = node[0]
        if kind == 'PROGRAM':
            for stmt in node[1]:
                self.generate(stmt)
        elif kind in ('DECL', 'ASSIGN'):
            _, name, expr = node
            t = self._gen_expr(expr)
            self._emit(f'{name} = {t}')
        elif kind == 'PRINT':
            t = self._gen_expr(node[1])
            self._emit(f'print {t}')
        elif kind == 'IF':
            _, cond, then_body, else_body = node
            t      = self._gen_expr(cond)
            l_else = self._lbl()
            l_end  = self._lbl()
            self._emit(f'ifFalse {t} goto {l_else}')
            for stmt in then_body:
                self.generate(stmt)
            self._emit(f'goto {l_end}')
            self._emit(f'{l_else}:')
            for stmt in else_body:
                self.generate(stmt)
            self._emit(f'{l_end}:')
        elif kind == 'WHILE':
            _, cond, body = node
            l_start = self._lbl()
            l_end   = self._lbl()
            self._emit(f'{l_start}:')
            t = self._gen_expr(cond)
            self._emit(f'ifFalse {t} goto {l_end}')
            for stmt in body:
                self.generate(stmt)
            self._emit(f'goto {l_start}')
            self._emit(f'{l_end}:')

    def _gen_expr(self, node):
        kind = node[0]
        if kind == 'NUM':
            return str(node[1])
        if kind == 'VAR':
            return node[1]
        if kind in ('BINOP', 'RELOP'):
            left  = self._gen_expr(node[2])
            right = self._gen_expr(node[3])
            t     = self._tmp()
            self._emit(f'{t} = {left} {node[1]} {right}')
            return t
        raise ValueError(f'Unknown expr node: {node}')


def generate_ir(source):
    """Full pipeline: source → AST → semantic check → TAC."""
    ast, sa = analyze(source)
    if sa.errors:
        for err in sa.errors:
            print(f'  Semantic ERROR: {err}')
    ir = IRGenerator()
    ir.generate(ast)
    return ir.code


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
    print('  PHASE 4 — Intermediate Code Gen (TAC)')
    print('=' * 50)
    ir_code = generate_ir(SAMPLE_SOURCE)
    print()
    for i, line in enumerate(ir_code, 1):
        print(f'  {i:>2}:  {line}')
    print(f'\nTotal instructions: {len(ir_code)}')
