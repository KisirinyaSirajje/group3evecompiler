"""
PHASE 3 — SEMANTIC ANALYSIS
Walks the AST to build a symbol table and detect semantic errors.
"""

from .phase2_parser import parse


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}
        self.errors       = []

    def analyze(self, node):
        kind = node[0]
        if kind == 'PROGRAM':
            for stmt in node[1]:
                self.analyze(stmt)
        elif kind == 'DECL':
            _, name, expr = node
            if name in self.symbol_table:
                self.errors.append(f"Variable '{name}' already declared")
            else:
                self.symbol_table[name] = 'int'
            self._check_expr(expr)
        elif kind == 'ASSIGN':
            _, name, expr = node
            if name not in self.symbol_table:
                self.errors.append(f"Undeclared variable '{name}'")
            self._check_expr(expr)
        elif kind == 'IF':
            _, cond, then_body, else_body = node
            self._check_expr(cond)
            for stmt in then_body:
                self.analyze(stmt)
            for stmt in else_body:
                self.analyze(stmt)
        elif kind == 'WHILE':
            _, cond, body = node
            self._check_expr(cond)
            for stmt in body:
                self.analyze(stmt)
        elif kind == 'PRINT':
            self._check_expr(node[1])

    def _check_expr(self, node):
        if node is None:
            return
        kind = node[0]
        if kind == 'VAR':
            if node[1] not in self.symbol_table:
                self.errors.append(f"Undeclared variable '{node[1]}'")
        elif kind in ('BINOP', 'RELOP'):
            self._check_expr(node[2])
            self._check_expr(node[3])


def analyze(source):
    """Full pipeline: source → tokens → AST → semantic check."""
    ast = parse(source)
    sa  = SemanticAnalyzer()
    sa.analyze(ast)
    return ast, sa
