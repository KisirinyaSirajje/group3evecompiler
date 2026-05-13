"""
PHASE 3 — SEMANTIC ANALYSIS
Walks the AST to build a symbol table and detect semantic errors.
Supports scoped symbol tables, functions, multiple types, and all
new constructs added by the expanded parser.
"""

from .phase2_parser import parse


class SemanticAnalyzer:
    def __init__(self):
        self._scopes    = [{}]   # stack; index 0 = global scope
        self.errors     = []
        self._functions = {}     # name → return_type

    # ── Scope helpers ──────────────────────────────────────────────

    @property
    def symbol_table(self):
        """Merged view of all scopes (for display)."""
        merged = {}
        for scope in self._scopes:
            merged.update(scope)
        return merged

    def _declare(self, name, dtype):
        if name in self._scopes[-1]:
            self.errors.append(f"Variable '{name}' already declared")
        else:
            self._scopes[-1][name] = dtype

    def _lookup(self, name):
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def _push_scope(self):
        self._scopes.append({})

    def _pop_scope(self):
        if len(self._scopes) > 1:
            self._scopes.pop()

    # ── Main analysis ──────────────────────────────────────────────

    def analyze(self, node):
        if node is None:
            return
        kind = node[0]

        if kind == 'PROGRAM':
            for stmt in node[1]:
                self.analyze(stmt)

        elif kind == 'FUNC_DEF':
            _, ret_type, name, params, body = node
            self._functions[name] = ret_type
            self._declare(name, ret_type)
            self._push_scope()
            for ptype, pname in params:
                self._declare(pname, ptype)
            for stmt in body:
                self.analyze(stmt)
            self._pop_scope()

        elif kind == 'DECL':
            _, name, expr, *rest = node
            dtype = rest[0] if rest else 'int'
            self._declare(name, dtype)
            if expr is not None:
                self._check_expr(expr)

        elif kind == 'MULTI_DECL':
            _, dtype, pairs = node
            for name, expr in pairs:
                self._declare(name, dtype)
                if expr is not None:
                    self._check_expr(expr)

        elif kind == 'ARRAY_DECL':
            _, dtype, name, size_expr, init = node
            self._declare(name, dtype + '[]')
            if size_expr is not None:
                self._check_expr(size_expr)

        elif kind == 'ASSIGN':
            _, name, expr = node
            if self._lookup(name) is None:
                self.errors.append(f"Undeclared variable '{name}'")
            self._check_expr(expr)

        elif kind == 'ARRAY_ASSIGN':
            _, name, idx, val = node
            if self._lookup(name) is None:
                self.errors.append(f"Undeclared variable '{name}'")
            self._check_expr(idx)
            self._check_expr(val)

        elif kind == 'COMPOUND_ASSIGN':
            _, op, name, expr = node
            if self._lookup(name) is None:
                self.errors.append(f"Undeclared variable '{name}'")
            self._check_expr(expr)

        elif kind == 'INCR':
            _, op, name, post = node
            if self._lookup(name) is None:
                self.errors.append(f"Undeclared variable '{name}'")

        elif kind == 'IF':
            _, cond, then_body, else_body = node
            self._check_expr(cond)
            self._push_scope()
            for stmt in then_body:
                self.analyze(stmt)
            self._pop_scope()
            self._push_scope()
            for stmt in else_body:
                self.analyze(stmt)
            self._pop_scope()

        elif kind == 'FOR':
            _, init, cond, update, body = node
            self._push_scope()
            if init is not None:
                self.analyze(init)
            if cond is not None:
                self._check_expr(cond)
            if update is not None:
                self.analyze(update)
            for stmt in body:
                self.analyze(stmt)
            self._pop_scope()

        elif kind == 'WHILE':
            _, cond, body = node
            self._check_expr(cond)
            self._push_scope()
            for stmt in body:
                self.analyze(stmt)
            self._pop_scope()

        elif kind == 'DO_WHILE':
            _, body, cond = node
            self._push_scope()
            for stmt in body:
                self.analyze(stmt)
            self._pop_scope()
            self._check_expr(cond)

        elif kind == 'SWITCH':
            _, expr, cases, default = node
            self._check_expr(expr)
            for case_val, case_stmts in cases:
                self._check_expr(case_val)
                self._push_scope()
                for stmt in case_stmts:
                    self.analyze(stmt)
                self._pop_scope()
            self._push_scope()
            for stmt in default:
                self.analyze(stmt)
            self._pop_scope()

        elif kind == 'PRINT':
            self._check_expr(node[1])

        elif kind == 'PRINTF':
            for arg in node[1]:
                self._check_expr(arg)

        elif kind == 'SCANF':
            for var in node[1]:
                if self._lookup(var) is None:
                    self.errors.append(f"Undeclared variable '{var}'")

        elif kind == 'CALL_STMT':
            _, name, args = node
            for arg in args:
                self._check_expr(arg)

        elif kind == 'RETURN':
            if node[1] is not None:
                self._check_expr(node[1])

        elif kind in ('BREAK', 'CONTINUE', 'EXPR_STMT'):
            pass

    def _check_expr(self, node):
        if node is None:
            return
        kind = node[0]
        if kind == 'VAR':
            if self._lookup(node[1]) is None:
                self.errors.append(f"Undeclared variable '{node[1]}'")
        elif kind in ('BINOP', 'RELOP', 'LOGOP'):
            self._check_expr(node[2])
            self._check_expr(node[3])
        elif kind == 'NOT':
            self._check_expr(node[1])
        elif kind == 'UNARY_MINUS':
            self._check_expr(node[1])
        elif kind in ('NUM', 'FLOAT_LIT', 'STRING', 'CHAR'):
            pass
        elif kind == 'INCR_EXPR':
            _, op, name, post = node
            if self._lookup(name) is None:
                self.errors.append(f"Undeclared variable '{name}'")
        elif kind == 'CALL':
            _, name, args = node
            for arg in args:
                self._check_expr(arg)
        elif kind == 'INDEX':
            _, name, idx = node
            if self._lookup(name) is None:
                self.errors.append(f"Undeclared variable '{name}'")
            self._check_expr(idx)
        elif kind == 'ARRAY_INIT':
            for item in node[1]:
                self._check_expr(item)


def analyze(source):
    """Full pipeline: source → tokens → AST → semantic check."""
    ast = parse(source)
    sa  = SemanticAnalyzer()
    sa.analyze(ast)
    return ast, sa
