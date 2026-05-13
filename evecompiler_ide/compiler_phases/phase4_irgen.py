"""
PHASE 4 — INTERMEDIATE CODE GENERATION
Converts the AST into Three-Address Code (TAC).
Supports all constructs added by the expanded parser and semantic analyzer.
"""

from .phase3_semantic import analyze


class IRGenerator:
    def __init__(self):
        self.code            = []
        self._tmp_count      = 0
        self._lbl_count      = 0
        self._break_stack    = []   # label to goto on break
        self._continue_stack = []   # label to goto on continue

    def _tmp(self):
        self._tmp_count += 1
        return f't{self._tmp_count}'

    def _lbl(self):
        self._lbl_count += 1
        return f'L{self._lbl_count}'

    def _emit(self, instr):
        self.code.append(instr)

    # ── Statement generation ──────────────────────────────────────

    def generate(self, node):
        if node is None:
            return
        kind = node[0]

        if kind == 'PROGRAM':
            for stmt in node[1]:
                self.generate(stmt)

        elif kind == 'FUNC_DEF':
            _, ret_type, name, params, body = node
            self._emit(f'func_begin {name}')
            for ptype, pname in params:
                self._emit(f'param {pname}')
            for stmt in body:
                self.generate(stmt)
            self._emit(f'func_end {name}')

        elif kind in ('DECL', 'ASSIGN'):
            _, name, expr, *_ = node
            if expr is None:
                self._emit(f'{name} = 0')
            else:
                t = self._gen_expr(expr)
                self._emit(f'{name} = {t}')

        elif kind == 'MULTI_DECL':
            _, dtype, pairs = node
            for name, expr in pairs:
                if expr is None:
                    self._emit(f'{name} = 0')
                else:
                    t = self._gen_expr(expr)
                    self._emit(f'{name} = {t}')

        elif kind == 'ARRAY_DECL':
            _, dtype, name, size_expr, init = node
            size = self._gen_expr(size_expr) if size_expr else '0'
            self._emit(f'array {name}[{size}]')
            if init is not None and init[0] == 'ARRAY_INIT':
                for i, item in enumerate(init[1]):
                    v = self._gen_expr(item)
                    self._emit(f'{name}[{i}] = {v}')

        elif kind == 'ARRAY_ASSIGN':
            _, name, idx, val = node
            i = self._gen_expr(idx)
            v = self._gen_expr(val)
            self._emit(f'{name}[{i}] = {v}')

        elif kind == 'COMPOUND_ASSIGN':
            _, op, name, expr = node
            val = self._gen_expr(expr)
            t   = self._tmp()
            self._emit(f'{t} = {name} {op} {val}')
            self._emit(f'{name} = {t}')

        elif kind == 'INCR':
            _, op, name, post = node
            arith = '+' if op == '++' else '-'
            t = self._tmp()
            self._emit(f'{t} = {name} {arith} 1')
            self._emit(f'{name} = {t}')

        elif kind == 'PRINT':
            t = self._gen_expr(node[1])
            self._emit(f'print {t}')

        elif kind == 'PRINTF':
            args    = node[1]
            non_str = [a for a in args if a[0] != 'STRING']
            if non_str:
                for a in non_str:
                    t = self._gen_expr(a)
                    self._emit(f'print {t}')
            elif args:
                self._emit(f'print {args[0][1]}')

        elif kind == 'SCANF':
            for var in node[1]:
                self._emit(f'read {var}')

        elif kind == 'CALL_STMT':
            _, name, args = node
            for a in args:
                t = self._gen_expr(a)
                self._emit(f'push_arg {t}')
            self._emit(f'call {name}')

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

        elif kind == 'FOR':
            _, init, cond, update, body = node
            l_start    = self._lbl()
            l_continue = self._lbl()
            l_end      = self._lbl()
            self._break_stack.append(l_end)
            self._continue_stack.append(l_continue)
            if init is not None:
                self.generate(init)
            self._emit(f'{l_start}:')
            t = self._gen_expr(cond)
            self._emit(f'ifFalse {t} goto {l_end}')
            for stmt in body:
                self.generate(stmt)
            self._emit(f'{l_continue}:')
            if update is not None:
                self.generate(update)
            self._emit(f'goto {l_start}')
            self._emit(f'{l_end}:')
            self._break_stack.pop()
            self._continue_stack.pop()

        elif kind == 'WHILE':
            _, cond, body = node
            l_start = self._lbl()
            l_end   = self._lbl()
            self._break_stack.append(l_end)
            self._continue_stack.append(l_start)
            self._emit(f'{l_start}:')
            t = self._gen_expr(cond)
            self._emit(f'ifFalse {t} goto {l_end}')
            for stmt in body:
                self.generate(stmt)
            self._emit(f'goto {l_start}')
            self._emit(f'{l_end}:')
            self._break_stack.pop()
            self._continue_stack.pop()

        elif kind == 'DO_WHILE':
            _, body, cond = node
            l_start = self._lbl()
            l_end   = self._lbl()
            self._break_stack.append(l_end)
            self._continue_stack.append(l_start)
            self._emit(f'{l_start}:')
            for stmt in body:
                self.generate(stmt)
            t = self._gen_expr(cond)
            self._emit(f'ifTrue {t} goto {l_start}')
            self._emit(f'{l_end}:')
            self._break_stack.pop()
            self._continue_stack.pop()

        elif kind == 'SWITCH':
            _, expr, cases, default = node
            val   = self._gen_expr(expr)
            l_end = self._lbl()
            clbls = [self._lbl() for _ in cases]
            l_def = self._lbl()
            self._break_stack.append(l_end)
            for i, (case_val, _) in enumerate(cases):
                cv = self._gen_expr(case_val)
                t  = self._tmp()
                self._emit(f'{t} = {val} == {cv}')
                self._emit(f'ifTrue {t} goto {clbls[i]}')
            self._emit(f'goto {l_def}')
            for i, (_, stmts) in enumerate(cases):
                self._emit(f'{clbls[i]}:')
                for stmt in stmts:
                    self.generate(stmt)
            self._emit(f'{l_def}:')
            for stmt in default:
                self.generate(stmt)
            self._emit(f'{l_end}:')
            self._break_stack.pop()

        elif kind == 'RETURN':
            _, expr = node
            if expr is not None:
                t = self._gen_expr(expr)
                self._emit(f'return {t}')
            else:
                self._emit('return')

        elif kind == 'BREAK':
            if self._break_stack:
                self._emit(f'goto {self._break_stack[-1]}')

        elif kind == 'CONTINUE':
            if self._continue_stack:
                self._emit(f'goto {self._continue_stack[-1]}')

        elif kind == 'EXPR_STMT':
            if node[1] is not None:
                self._gen_expr(node[1])

    # ── Expression generation ─────────────────────────────────────

    def _gen_expr(self, node):
        kind = node[0]
        if kind == 'NUM':
            return str(node[1])
        if kind == 'FLOAT_LIT':
            return str(node[1])
        if kind == 'STRING':
            return node[1]
        if kind == 'CHAR':
            return node[1]
        if kind == 'VAR':
            return node[1]
        if kind in ('BINOP', 'RELOP'):
            left  = self._gen_expr(node[2])
            right = self._gen_expr(node[3])
            t     = self._tmp()
            self._emit(f'{t} = {left} {node[1]} {right}')
            return t
        if kind == 'LOGOP':
            left  = self._gen_expr(node[2])
            right = self._gen_expr(node[3])
            t     = self._tmp()
            self._emit(f'{t} = {left} {node[1]} {right}')
            return t
        if kind == 'NOT':
            val = self._gen_expr(node[1])
            t   = self._tmp()
            self._emit(f'{t} = ! {val}')
            return t
        if kind == 'UNARY_MINUS':
            val = self._gen_expr(node[1])
            t   = self._tmp()
            self._emit(f'{t} = 0 - {val}')
            return t
        if kind == 'INCR_EXPR':
            _, op, name, post = node
            arith = '+' if op == '++' else '-'
            t     = self._tmp()
            if post:
                old = self._tmp()
                self._emit(f'{old} = {name}')
                self._emit(f'{t} = {name} {arith} 1')
                self._emit(f'{name} = {t}')
                return old
            else:
                self._emit(f'{t} = {name} {arith} 1')
                self._emit(f'{name} = {t}')
                return t
        if kind == 'CALL':
            _, name, args = node
            for a in args:
                at = self._gen_expr(a)
                self._emit(f'push_arg {at}')
            t = self._tmp()
            self._emit(f'{t} = call {name}')
            return t
        if kind == 'INDEX':
            _, name, idx = node
            i = self._gen_expr(idx)
            t = self._tmp()
            self._emit(f'{t} = {name}[{i}]')
            return t
        raise ValueError(f'Unknown expr node: {node}')


def generate_ir(source):
    """Full pipeline: source → AST → semantic check → TAC."""
    ast, sa = analyze(source)
    if sa.errors:
        raise RuntimeError(f"Semantic errors: {sa.errors}")
    ir = IRGenerator()
    ir.generate(ast)
    return ir.code
