"""
PHASE 1 — LEXICAL ANALYSIS
Converts source code into a flat list of (type, value) tokens.
Run standalone: python phase1_lexer.py
"""

import re

TOKEN_SPEC = [
    ('KEYWORD',  r'\b(int|if|else|while|print|return)\b'),
    ('NUMBER',   r'\d+'),
    ('ID',       r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('RELOP',    r'[<>]=?|==|!='),
    ('OP',       r'[+\-*/]'),
    ('ASSIGN',   r'='),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('SEMI',     r';'),
    ('SKIP',     r'[ \t\n\r]+'),
    ('MISMATCH', r'.'),
]

TOKEN_RE = re.compile('|'.join(f'(?P<{name}>{pat})' for name, pat in TOKEN_SPEC))


def tokenize(source):
    """Tokenize source code string. Returns list of (kind, value) tuples."""
    tokens = []
    for m in TOKEN_RE.finditer(source):
        kind  = m.lastgroup
        value = m.group()
        if kind == 'SKIP':
            continue
        if kind == 'MISMATCH':
            raise SyntaxError(f'[Lexer] Unexpected character: {value!r}')
        tokens.append((kind, value))
    tokens.append(('EOF', ''))
    return tokens


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
    print('  PHASE 1 — Lexical Analysis')
    print('=' * 50)
    print('\nSource:\n', SAMPLE_SOURCE)
    tokens = tokenize(SAMPLE_SOURCE)
    print(f'{"Token Type":<14}  Value')
    print('-' * 30)
    for kind, value in tokens[:-1]:   # exclude EOF
        print(f'  {kind:<12}  {value!r}')
    print(f'\nTotal tokens: {len(tokens) - 1}')
