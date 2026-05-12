"""
PHASE 2 — SYNTAX ANALYSIS
Parses tokens into an Abstract Syntax Tree (AST) using a recursive-descent parser.
Run standalone: python phase2_parser.py
"""

from phase1_lexer import tokenize


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ── helpers ──────────────────────────────────────────────

    def peek(self):
        return self.tokens[self.pos]

    def consume(self, expected_kind=None, expected_value=None):
        tok = self.tokens[self.pos]
        if expected_kind and tok[0] != expected_kind:
            raise SyntaxError(
                f'[Parser] Expected {expected_kind!r}, got {tok[0]!r} ({tok[1]!r})')
        if expected_value and tok[1] != expected_value:
            raise SyntaxError(
                f'[Parser] Expected {expected_value!r}, got {tok[1]!r}')
        self.pos += 1
        return tok

    # ── grammar rules ────────────────────────────────────────

    def parse(self):
        stmts = []
        while self.peek()[0] != 'EOF':
            stmts.append(self.stmt())
        return ('PROGRAM', stmts)

    def stmt(self):
        tok = self.peek()
        if tok == ('KEYWORD', 'int'):
            return self.decl()
        if tok == ('KEYWORD', 'if'):
            return self.if_stmt()
        if tok == ('KEYWORD', 'while'):
            return self.while_stmt()
        if tok == ('KEYWORD', 'print'):
            return self.print_stmt()
        if tok[0] == 'ID':
            return self.assign()
        raise SyntaxError(f'[Parser] Unexpected token: {tok}')

    def decl(self):
        self.consume('KEYWORD', 'int')
        name = self.consume('ID')[1]
        self.consume('ASSIGN', '=')
        expr = self.expr()
        self.consume('SEMI')
        return ('DECL', name, expr)

    def assign(self):
        name = self.consume('ID')[1]
        self.consume('ASSIGN', '=')
        expr = self.expr()
        self.consume('SEMI')
        return ('ASSIGN', name, expr)

    def if_stmt(self):
        self.consume('KEYWORD', 'if')
        self.consume('LPAREN')
        cond = self.rel_expr()
        self.consume('RPAREN')
        self.consume('LBRACE')
        then_body = self.block()
        self.consume('RBRACE')
        else_body = []
        if self.peek() == ('KEYWORD', 'else'):
            self.consume('KEYWORD', 'else')
            self.consume('LBRACE')
            else_body = self.block()
            self.consume('RBRACE')
        return ('IF', cond, then_body, else_body)

    def while_stmt(self):
        self.consume('KEYWORD', 'while')
        self.consume('LPAREN')
        cond = self.rel_expr()
        self.consume('RPAREN')
        self.consume('LBRACE')
        body = self.block()
        self.consume('RBRACE')
        return ('WHILE', cond, body)

    def print_stmt(self):
        self.consume('KEYWORD', 'print')
        self.consume('LPAREN')
        expr = self.expr()
        self.consume('RPAREN')
        self.consume('SEMI')
        return ('PRINT', expr)

    def block(self):
        stmts = []
        while self.peek()[0] not in ('RBRACE', 'EOF'):
            stmts.append(self.stmt())
        return stmts

    def rel_expr(self):
        left = self.expr()
        if self.peek()[0] == 'RELOP':
            op    = self.consume('RELOP')[1]
            right = self.expr()
            return ('RELOP', op, left, right)
        return left

    def expr(self):
        node = self.term()
        while self.peek()[1] in ('+', '-'):
            op    = self.consume('OP')[1]
            right = self.term()
            node  = ('BINOP', op, node, right)
        return node

    def term(self):
        node = self.factor()
        while self.peek()[1] in ('*', '/'):
            op    = self.consume('OP')[1]
            right = self.factor()
            node  = ('BINOP', op, node, right)
        return node

    def factor(self):
        tok = self.peek()
        if tok[0] == 'NUMBER':
            self.consume()
            return ('NUM', int(tok[1]))
        if tok[0] == 'ID':
            self.consume()
            return ('VAR', tok[1])
        if tok[0] == 'LPAREN':
            self.consume('LPAREN')
            node = self.expr()
            self.consume('RPAREN')
            return node
        raise SyntaxError(f'[Parser] Unexpected token in expression: {tok}')


def parse(source):
    """Full pipeline: source → tokens → AST."""
    tokens = tokenize(source)
    return Parser(tokens).parse()


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
    from pprint import pformat
    print('=' * 50)
    print('  PHASE 2 — Syntax Analysis (AST)')
    print('=' * 50)
    ast = parse(SAMPLE_SOURCE)
    print(f'\nAST — {len(ast[1])} top-level statements:\n')
    for i, node in enumerate(ast[1], 1):
        print(f'  [{i}] {pformat(node, width=60)}')
