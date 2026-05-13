"""
PHASE 1 — LEXICAL ANALYSIS
Converts source code into tokens supporting a broad C subset.
Handles: types, keywords, operators, strings, chars, floats,
         comments, preprocessor directives, ++/--, +=/-=, &&/||/!
"""

import re

TYPE_KEYWORDS = {
    'int', 'float', 'double', 'char', 'void', 'bool',
    'unsigned', 'long', 'short',
}

TOKEN_SPEC = [
    ('COMMENT_ML', r'/\*.*?\*/'),
    ('COMMENT_SL', r'//[^\n]*'),
    ('PREPROC',    r'#[^\n]*'),
    ('STRING',     r'"(?:[^"\\]|\\.)*"'),
    ('CHAR_LIT',   r"'(?:[^'\\]|\\.)'"),
    ('FLOAT',      r'\d+\.\d+|\.\d+'),
    ('NUMBER',     r'\d+'),
    ('KEYWORD',    r'\b(int|float|double|char|void|bool|unsigned|long|short|'
                   r'if|else|for|while|do|switch|case|default|'
                   r'break|continue|return|printf|scanf|print)\b'),
    ('ID',         r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('INCR',       r'\+\+|--'),
    ('COMPOUND',   r'[+\-*/&|%]='),
    ('LOGOP',      r'&&|\|\|'),
    ('NOT',        r'!'),
    ('RELOP',      r'[<>]=?|==|!='),
    ('OP',         r'[+\-*/%]'),
    ('ASSIGN',     r'='),
    ('LPAREN',     r'\('),
    ('RPAREN',     r'\)'),
    ('LBRACE',     r'\{'),
    ('RBRACE',     r'\}'),
    ('LBRACKET',   r'\['),
    ('RBRACKET',   r'\]'),
    ('COMMA',      r','),
    ('SEMI',       r';'),
    ('COLON',      r':'),
    ('AMPERSAND',  r'&'),
    ('SKIP',       r'[ \t\n\r]+'),
    ('MISMATCH',   r'.'),
]

TOKEN_RE = re.compile(
    '|'.join(f'(?P<{name}>{pat})' for name, pat in TOKEN_SPEC),
    re.DOTALL
)


def tokenize(source):
    """Tokenize source. Returns list of (kind, value, line) tuples."""
    tokens = []
    line = 1
    for m in TOKEN_RE.finditer(source):
        kind  = m.lastgroup
        value = m.group()
        if kind == 'SKIP':
            line += value.count('\n')
            continue
        if kind in ('COMMENT_ML', 'COMMENT_SL', 'PREPROC'):
            line += value.count('\n')
            continue
        if kind == 'MISMATCH':
            raise SyntaxError(f'[Lexer] Unexpected character: {value!r}')
        tokens.append((kind, value, line))
    tokens.append(('EOF', '', line))
    return tokens
