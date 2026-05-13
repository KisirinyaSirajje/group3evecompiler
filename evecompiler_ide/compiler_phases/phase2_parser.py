"""
PHASE 2 — SYNTAX ANALYSIS
Recursive-descent parser supporting a broad C subset:
  - Multiple types (int, float, double, char, void, bool)
  - for / while / do-while / if-else-if / switch-case
  - Functions (definitions and calls)
  - return / break / continue
  - printf / scanf / print
  - ++/--, +=/-=/*=//=/%=
  - && / || / !  / unary minus
  - Arrays (basic), type casts (ignored)
  - #include / comments (skipped by lexer)
"""

from .phase1_lexer import tokenize, TYPE_KEYWORDS


class Parser:
    def __init__(self, tokens):
        self._token_lines = [t[2] if len(t) > 2 else 1 for t in tokens]
        self.tokens = [(t[0], t[1]) for t in tokens]
        self.pos    = 0
        self._cur_line = 1
        self._prev_line = 1

    def peek(self, offset=0):
        pos = self.pos + offset
        return self.tokens[pos] if pos < len(self.tokens) else ('EOF', '')

    def consume(self, expected_kind=None, expected_value=None):
        tok = self.tokens[self.pos]
        tok_line = self._token_lines[self.pos] if self.pos < len(self._token_lines) else self._cur_line
        if expected_kind and tok[0] != expected_kind:
            # For missing semicolon, report the line where semicolon was expected (previous line)
            error_line = self._cur_line if expected_kind == 'SEMI' else tok_line
            raise SyntaxError(
                f'[Parser] Line {error_line}: Expected {expected_kind!r}, got {tok[0]!r} ({tok[1]!r})')
        if expected_value and tok[1] != expected_value:
            error_line = self._cur_line if expected_value == ';' else tok_line
            raise SyntaxError(
                f'[Parser] Line {error_line}: Expected {expected_value!r}, got {tok[1]!r}')
        self._prev_line = self._cur_line
        self._cur_line = tok_line
        self.pos += 1
        return tok

    # ── Type helpers ──────────────────────────────────────────────

    def _is_type(self):
        tok = self.peek()
        return tok[0] == 'KEYWORD' and tok[1] in TYPE_KEYWORDS

    def _parse_type(self):
        """Consume one or more type keywords and optional pointer *."""
        parts = []
        while self.peek()[0] == 'KEYWORD' and self.peek()[1] in TYPE_KEYWORDS:
            parts.append(self.consume()[1])
        while self.peek()[0] == 'OP' and self.peek()[1] == '*':
            self.consume()
            parts.append('*')
        return ' '.join(parts) if parts else 'int'

    def _is_func_def(self):
        """Lookahead: type ... ID ( → function definition."""
        save = self.pos
        while self.peek()[0] == 'KEYWORD' and self.peek()[1] in TYPE_KEYWORDS:
            self.pos += 1
        while self.peek()[0] == 'OP' and self.peek()[1] == '*':
            self.pos += 1
        is_func = (self.peek()[0] in ('ID', 'KEYWORD') and
                   self.peek(1)[0] == 'LPAREN')
        self.pos = save
        return is_func

    # ── Top-level ────────────────────────────────────────────────

    def parse(self):
        stmts = []
        while self.peek()[0] != 'EOF':
            if self._is_type() and self._is_func_def():
                stmts.append(self.func_def())
            elif self._is_type():
                stmts.append(self.decl())
            else:
                s = self.stmt()
                if s is not None:
                    stmts.append(s)
        return ('PROGRAM', stmts)

    # ── Function definition ───────────────────────────────────────

    def func_def(self):
        return_type = self._parse_type()
        name = (self.consume('ID') if self.peek()[0] == 'ID'
                else self.consume('KEYWORD'))[1]
        self.consume('LPAREN')
        params = self._parse_params()
        self.consume('RPAREN')
        self.consume('LBRACE')
        body = self.block()
        self.consume('RBRACE')
        return ('FUNC_DEF', return_type, name, params, body)

    def _parse_params(self):
        params = []
        if self.peek()[0] == 'RPAREN':
            return params
        if (self.peek() == ('KEYWORD', 'void') and
                self.peek(1)[0] == 'RPAREN'):
            self.consume()
            return params
        while True:
            ptype = self._parse_type()
            pname = self.consume('ID')[1]
            if self.peek()[0] == 'LBRACKET':
                self.consume('LBRACKET')
                self.consume('RBRACKET')
                ptype += '[]'
            params.append((ptype, pname))
            if self.peek()[0] != 'COMMA':
                break
            self.consume('COMMA')
        return params

    # ── Block ─────────────────────────────────────────────────────

    def block(self):
        stmts = []
        while self.peek()[0] not in ('RBRACE', 'EOF'):
            s = self.stmt()
            if s is not None:
                stmts.append(s)
        return stmts

    def _parse_body(self):
        """Braced block or single statement."""
        if self.peek()[0] == 'LBRACE':
            self.consume('LBRACE')
            body = self.block()
            self.consume('RBRACE')
            return body
        s = self.stmt()
        return [s] if s is not None else []

    # ── Statements ────────────────────────────────────────────────

    def stmt(self):
        tok = self.peek()
        if self._is_type():
            return self.decl()
        if tok == ('KEYWORD', 'if'):
            return self.if_stmt()
        if tok == ('KEYWORD', 'for'):
            return self.for_stmt()
        if tok == ('KEYWORD', 'while'):
            return self.while_stmt()
        if tok == ('KEYWORD', 'do'):
            return self.do_while_stmt()
        if tok == ('KEYWORD', 'switch'):
            return self.switch_stmt()
        if tok == ('KEYWORD', 'return'):
            return self.return_stmt()
        if tok == ('KEYWORD', 'break'):
            self.consume()
            self.consume('SEMI')
            return ('BREAK',)
        if tok == ('KEYWORD', 'continue'):
            self.consume()
            self.consume('SEMI')
            return ('CONTINUE',)
        if tok == ('KEYWORD', 'printf'):
            return self.printf_stmt()
        if tok == ('KEYWORD', 'scanf'):
            return self.scanf_stmt()
        if tok == ('KEYWORD', 'print'):
            return self.print_stmt()
        if tok[0] == 'INCR':
            op   = self.consume('INCR')[1]
            name = self.consume('ID')[1]
            self.consume('SEMI')
            return ('INCR', op, name, False, self._cur_line)
        if tok[0] == 'ID':
            return self._id_stmt()
        if tok[0] == 'SEMI':
            self.consume()
            return None
        raise SyntaxError(f'[Parser] Line {self._cur_line}: Unexpected token: {tok}')

    def _id_stmt(self):
        name = self.consume('ID')[1]
        tok  = self.peek()
        if tok[0] == 'LPAREN':
            args = self._parse_call_args()
            self.consume('SEMI')
            return ('CALL_STMT', name, args)
        if tok[0] == 'LBRACKET':
            self.consume('LBRACKET')
            idx = self.expr()
            self.consume('RBRACKET')
            self.consume('ASSIGN', '=')
            val = self.expr()
            self.consume('SEMI')
            return ('ARRAY_ASSIGN', name, idx, val, self._cur_line)
        if tok[0] == 'INCR':
            op = self.consume('INCR')[1]
            self.consume('SEMI')
            return ('INCR', op, name, True, self._cur_line)
        if tok[0] == 'COMPOUND':
            op_tok   = self.consume('COMPOUND')[1]
            arith_op = op_tok[0]
            val      = self.expr()
            self.consume('SEMI')
            return ('COMPOUND_ASSIGN', arith_op, name, val, self._cur_line)
        if tok[0] == 'ASSIGN':
            self.consume('ASSIGN', '=')
            val = self.expr()
            self.consume('SEMI')
            return ('ASSIGN', name, val, self._cur_line)
        raise SyntaxError(
            f'[Parser] Line {self._cur_line}: Unexpected token after ID {name!r}: {tok}')

    # ── Declaration ───────────────────────────────────────────────

    def decl(self):
        dtype = self._parse_type()
        name  = self.consume('ID')[1]
        # Array declaration
        if self.peek()[0] == 'LBRACKET':
            self.consume('LBRACKET')
            size_expr = None
            if self.peek()[0] != 'RBRACKET':
                size_expr = self.expr()
            self.consume('RBRACKET')
            init = None
            if self.peek()[0] == 'ASSIGN':
                self.consume('ASSIGN', '=')
                init = self._parse_array_init()
            self.consume('SEMI')
            return ('ARRAY_DECL', dtype, name, size_expr, init)
        # Normal variable(s)
        expr = None
        if self.peek()[0] == 'ASSIGN':
            self.consume('ASSIGN', '=')
            expr = self.expr()
        extras = []
        while self.peek()[0] == 'COMMA':
            self.consume('COMMA')
            extra_name = self.consume('ID')[1]
            extra_expr = None
            if self.peek()[0] == 'ASSIGN':
                self.consume('ASSIGN', '=')
                extra_expr = self.expr()
            extras.append((extra_name, extra_expr))
        self.consume('SEMI')
        if not extras:
            return ('DECL', name, expr, dtype, self._cur_line)
        return ('MULTI_DECL', dtype, [(name, expr)] + extras)

    def _parse_array_init(self):
        if self.peek()[0] == 'LBRACE':
            self.consume('LBRACE')
            items = []
            while self.peek()[0] not in ('RBRACE', 'EOF'):
                items.append(self.expr())
                if self.peek()[0] == 'COMMA':
                    self.consume('COMMA')
            self.consume('RBRACE')
            return ('ARRAY_INIT', items)
        return self.expr()

    # ── Control flow ──────────────────────────────────────────────

    def if_stmt(self):
        self.consume('KEYWORD', 'if')
        self.consume('LPAREN')
        cond = self.cond_expr()
        self.consume('RPAREN')
        then_body = self._parse_body()
        else_body = []
        if self.peek() == ('KEYWORD', 'else'):
            self.consume('KEYWORD', 'else')
            if self.peek() == ('KEYWORD', 'if'):
                else_body = [self.if_stmt()]
            else:
                else_body = self._parse_body()
        return ('IF', cond, then_body, else_body)

    def for_stmt(self):
        self.consume('KEYWORD', 'for')
        self.consume('LPAREN')
        # init
        if self.peek()[0] == 'SEMI':
            init = None
            self.consume('SEMI')
        elif self._is_type():
            dtype = self._parse_type()
            iname = self.consume('ID')[1]
            iexpr = None
            if self.peek()[0] == 'ASSIGN':
                self.consume('ASSIGN', '=')
                iexpr = self.expr()
            init = ('DECL', iname, iexpr, dtype, self._cur_line)
            self.consume('SEMI')
        else:
            init = self._for_expr()
            self.consume('SEMI')
        # condition
        if self.peek()[0] == 'SEMI':
            cond = ('NUM', 1)
            self.consume('SEMI')
        else:
            cond = self.cond_expr()
            self.consume('SEMI')
        # update
        update = None if self.peek()[0] == 'RPAREN' else self._for_expr()
        self.consume('RPAREN')
        body = self._parse_body()
        return ('FOR', init, cond, update, body)

    def _for_expr(self):
        """Parse one for-init/update expression (no trailing SEMI consumed)."""
        if self.peek()[0] == 'INCR':
            op   = self.consume('INCR')[1]
            name = self.consume('ID')[1]
            return ('INCR', op, name, False, self._cur_line)
        name = self.consume('ID')[1]
        tok  = self.peek()
        if tok[0] == 'INCR':
            op = self.consume('INCR')[1]
            return ('INCR', op, name, True, self._cur_line)
        if tok[0] == 'COMPOUND':
            op_tok = self.consume('COMPOUND')[1]
            return ('COMPOUND_ASSIGN', op_tok[0], name, self.expr(), self._cur_line)
        if tok[0] == 'ASSIGN':
            self.consume('ASSIGN', '=')
            return ('ASSIGN', name, self.expr(), self._cur_line)
        return ('EXPR_STMT', ('VAR', name))

    def while_stmt(self):
        self.consume('KEYWORD', 'while')
        self.consume('LPAREN')
        cond = self.cond_expr()
        self.consume('RPAREN')
        body = self._parse_body()
        return ('WHILE', cond, body)

    def do_while_stmt(self):
        self.consume('KEYWORD', 'do')
        body = self._parse_body()
        self.consume('KEYWORD', 'while')
        self.consume('LPAREN')
        cond = self.cond_expr()
        self.consume('RPAREN')
        self.consume('SEMI')
        return ('DO_WHILE', body, cond)

    def switch_stmt(self):
        self.consume('KEYWORD', 'switch')
        self.consume('LPAREN')
        expr = self.expr()
        self.consume('RPAREN')
        self.consume('LBRACE')
        cases   = []
        default = []
        while self.peek()[0] not in ('RBRACE', 'EOF'):
            if self.peek() == ('KEYWORD', 'case'):
                self.consume('KEYWORD', 'case')
                val   = self.expr()
                self.consume('COLON')
                stmts = []
                while (self.peek() not in [('KEYWORD', 'case'),
                                           ('KEYWORD', 'default')]
                       and self.peek()[0] not in ('RBRACE', 'EOF')):
                    s = self.stmt()
                    if s is not None:
                        stmts.append(s)
                cases.append((val, stmts))
            elif self.peek() == ('KEYWORD', 'default'):
                self.consume('KEYWORD', 'default')
                self.consume('COLON')
                while self.peek()[0] not in ('RBRACE', 'EOF'):
                    s = self.stmt()
                    if s is not None:
                        default.append(s)
            else:
                break
        self.consume('RBRACE')
        return ('SWITCH', expr, cases, default)

    def return_stmt(self):
        self.consume('KEYWORD', 'return')
        if self.peek()[0] == 'SEMI':
            self.consume('SEMI')
            return ('RETURN', None)
        expr = self.expr()
        self.consume('SEMI')
        return ('RETURN', expr)

    # ── I/O statements ────────────────────────────────────────────

    def printf_stmt(self):
        self.consume('KEYWORD', 'printf')
        self.consume('LPAREN')
        args = []
        while self.peek()[0] not in ('RPAREN', 'EOF'):
            args.append(self.expr())
            if self.peek()[0] == 'COMMA':
                self.consume('COMMA')
        self.consume('RPAREN')
        self.consume('SEMI')
        return ('PRINTF', args)

    def scanf_stmt(self):
        self.consume('KEYWORD', 'scanf')
        self.consume('LPAREN')
        vars_ = []
        first = True
        while self.peek()[0] not in ('RPAREN', 'EOF'):
            if first and self.peek()[0] == 'STRING':
                self.consume('STRING')
                first = False
                continue
            if self.peek()[0] == 'COMMA':
                self.consume('COMMA')
                first = False
                continue
            if self.peek()[0] == 'AMPERSAND':
                self.consume('AMPERSAND')
            if self.peek()[0] == 'ID':
                vars_.append(self.consume('ID')[1])
            else:
                self.consume()
            first = False
        self.consume('RPAREN')
        self.consume('SEMI')
        return ('SCANF', vars_)

    def print_stmt(self):
        self.consume('KEYWORD', 'print')
        self.consume('LPAREN')
        expr = self.expr()
        self.consume('RPAREN')
        self.consume('SEMI')
        return ('PRINT', expr)

    def _parse_call_args(self):
        self.consume('LPAREN')
        args = []
        while self.peek()[0] not in ('RPAREN', 'EOF'):
            args.append(self.expr())
            if self.peek()[0] == 'COMMA':
                self.consume('COMMA')
        self.consume('RPAREN')
        return args

    # ── Expressions (precedence: or > and > not > rel > add > mul > unary) ──

    def cond_expr(self):
        return self.or_expr()

    def or_expr(self):
        node = self.and_expr()
        while self.peek() == ('LOGOP', '||'):
            op    = self.consume('LOGOP')[1]
            right = self.and_expr()
            node  = ('LOGOP', op, node, right)
        return node

    def and_expr(self):
        node = self.not_expr()
        while self.peek() == ('LOGOP', '&&'):
            op    = self.consume('LOGOP')[1]
            right = self.not_expr()
            node  = ('LOGOP', op, node, right)
        return node

    def not_expr(self):
        if self.peek()[0] == 'NOT':
            self.consume('NOT')
            return ('NOT', self.not_expr())
        return self.rel_expr()

    def rel_expr(self):
        left = self.expr()
        if self.peek()[0] == 'RELOP':
            op    = self.consume('RELOP')[1]
            right = self.expr()
            return ('RELOP', op, left, right)
        return left

    def expr(self):
        node = self.term()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('+', '-'):
            op    = self.consume('OP')[1]
            right = self.term()
            node  = ('BINOP', op, node, right)
        return node

    def term(self):
        node = self.unary()
        while self.peek()[0] == 'OP' and self.peek()[1] in ('*', '/', '%'):
            op    = self.consume('OP')[1]
            right = self.unary()
            node  = ('BINOP', op, node, right)
        return node

    def unary(self):
        tok = self.peek()
        if tok[0] == 'OP' and tok[1] == '-':
            self.consume('OP')
            return ('UNARY_MINUS', self.unary())
        if tok[0] == 'INCR':
            op   = self.consume('INCR')[1]
            name = self.consume('ID')[1]
            return ('INCR_EXPR', op, name, False, self._cur_line)
        return self.factor()

    def factor(self):
        tok = self.peek()
        if tok[0] == 'NUMBER':
            self.consume()
            return ('NUM', int(tok[1]))
        if tok[0] == 'FLOAT':
            self.consume()
            return ('FLOAT_LIT', float(tok[1]))
        if tok[0] == 'STRING':
            self.consume()
            return ('STRING', tok[1])
        if tok[0] == 'CHAR_LIT':
            self.consume()
            return ('CHAR', tok[1])
        if tok[0] == 'ID':
            self.consume()
            name = tok[1]
            if self.peek()[0] == 'LPAREN':
                args = self._parse_call_args()
                return ('CALL', name, args)
            if self.peek()[0] == 'LBRACKET':
                self.consume('LBRACKET')
                idx = self.expr()
                self.consume('RBRACKET')
                return ('INDEX', name, idx, self._cur_line)
            if self.peek()[0] == 'INCR':
                op = self.consume('INCR')[1]
                return ('INCR_EXPR', op, name, True, self._cur_line)
            return ('VAR', name, self._cur_line)
        if tok[0] == 'LPAREN':
            self.consume('LPAREN')
            # type cast: (type) expr — parse and discard the cast
            if self._is_type():
                self._parse_type()
                self.consume('RPAREN')
                return self.unary()
            node = self.cond_expr()
            self.consume('RPAREN')
            return node
        raise SyntaxError(f'[Parser] Line {self._cur_line}: Unexpected token in expression: {tok}')


def parse(source):
    """Full pipeline: source → tokens → AST."""
    tokens = tokenize(source)
    return Parser(tokens).parse()
