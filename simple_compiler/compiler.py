"""
compiler.py — Orchestrator
Runs all 6 compiler phases in sequence.
Run: python compiler.py

Individual phases can also be run on their own:
  python phase1_lexer.py
  python phase2_parser.py
  python phase3_semantic.py
  python phase4_irgen.py
  python phase5_optimizer.py
  python phase6_codegen.py
"""

from pprint import pformat

from simple_compiler.phase1_lexer     import tokenize
from simple_compiler.phase2_parser    import Parser
from simple_compiler.phase3_semantic  import SemanticAnalyzer
from simple_compiler.phase4_irgen     import IRGenerator
from simple_compiler.phase5_optimizer import optimize
from simple_compiler.phase6_codegen   import code_gen

# =============================================================
#  Compiler Pipeline  —  mini-C language
#  Phase 1 → phase1_lexer.py
#  Phase 2 → phase2_parser.py
#  Phase 3 → phase3_semantic.py
#  Phase 4 → phase4_irgen.py
#  Phase 5 → phase5_optimizer.py
#  Phase 6 → phase6_codegen.py
# =============================================================

SOURCE = """\
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


def banner(phase_num, title):
    w = 58
    print(f'\n{"─" * w}')
    print(f'  PHASE {phase_num} — {title}')
    print('─' * w)


def main():
    print('=' * 58)
    print('  SIMPLE COMPILER  —  mini-C language')
    print('=' * 58)
    print('\nSource code:')
    print(SOURCE)

    # ── Phase 1: Lexical Analysis ────────────────────────────
    banner(1, 'Lexical Analysis  (Tokens)')
    tokens = tokenize(SOURCE)
    for kind, value in tokens[:-1]:
        print(f'  {kind:<12}  {value!r}')

    # ── Phase 2: Syntax Analysis ─────────────────────────────
    banner(2, 'Syntax Analysis  (AST)')
    ast = Parser(tokens).parse()
    for node in ast[1]:
        print(' ', pformat(node, width=60))

    # ── Phase 3: Semantic Analysis ───────────────────────────
    banner(3, 'Semantic Analysis  (Symbol Table)')
    sem = SemanticAnalyzer()
    sem.analyze(ast)
    if sem.errors:
        for err in sem.errors:
            print(f'  ERROR: {err}')
    else:
        print('  No semantic errors detected.')
    print('\n  Symbol Table:')
    for name, typ in sem.symbol_table.items():
        print(f'    {name:<12}  {typ}')

    # ── Phase 4: Intermediate Code Generation ────────────────
    banner(4, 'Intermediate Code Gen  (Three-Address Code)')
    ir = IRGenerator()
    ir.generate(ast)
    for line in ir.code:
        print(f'  {line}')

    # ── Phase 5: Code Optimization ───────────────────────────
    banner(5, 'Code Optimization  (Constant Folding & Propagation)')
    opt_ir = optimize(ir.code)
    for line in opt_ir:
        print(f'  {line}')

    # ── Phase 6: Code Generation ─────────────────────────────
    banner(6, 'Code Generation  (Pseudo-Assembly)')
    asm = code_gen(opt_ir)
    for line in asm:
        print(f'  {line}')

    print(f'\n{"=" * 58}')
    print('  Compilation complete.')
    print('=' * 58)


if __name__ == '__main__':
    main()

