"""
EveCompiler CLI — Command-line Interface
Compile mini-C code and get detailed error reports and output
"""

import sys
import os
from pathlib import Path
from compiler_phases.phase1_lexer import tokenize
from compiler_phases.phase2_parser import Parser
from compiler_phases.phase3_semantic import SemanticAnalyzer
from compiler_phases.phase4_irgen import IRGenerator
from compiler_phases.phase5_optimizer import optimize
from compiler_phases.phase6_codegen import code_gen


def ast_to_json(node):
    """Convert AST tuple tree to a JSON-serialisable dict for visualisation."""
    if node is None:
        return None
    if not isinstance(node, tuple):
        return {'label': str(node), 'children': []}
    kind = node[0]

    def wrap(label, *children):
        return {'label': label, 'children': [c for c in children if c is not None]}

    def expr_node(n):
        if n is None:
            return None
        if not isinstance(n, tuple):
            return {'label': str(n), 'children': []}
        k = n[0]
        if k == 'NUM':
            return wrap(str(n[1]))
        if k == 'FLOAT_LIT':
            return wrap(str(n[1]))
        if k == 'STRING':
            return wrap(n[1])
        if k == 'CHAR':
            return wrap(n[1])
        if k == 'VAR':
            return wrap(f'VAR: {n[1]}')
        if k in ('BINOP', 'RELOP'):
            return wrap(f'OP: {n[1]}', expr_node(n[2]), expr_node(n[3]))
        if k == 'LOGOP':
            return wrap(f'LOGOP: {n[1]}', expr_node(n[2]), expr_node(n[3]))
        if k == 'NOT':
            return wrap('!', expr_node(n[1]))
        if k == 'UNARY_MINUS':
            return wrap('UNARY -', expr_node(n[1]))
        if k == 'INCR_EXPR':
            return wrap(f'{"POST" if n[3] else "PRE"}{n[1]}: {n[2]}')
        if k == 'CALL':
            args = [expr_node(a) for a in n[2]]
            return {'label': f'CALL: {n[1]}', 'children': args}
        if k == 'INDEX':
            return wrap(f'INDEX: {n[1]}', expr_node(n[2]))
        return wrap(str(n))

    def stmt_node(n):
        return ast_to_json(n)

    def stmts(lst):
        return [stmt_node(s) for s in (lst or []) if s is not None]

    if kind == 'PROGRAM':
        return {'label': 'PROGRAM', 'children': stmts(node[1])}
    if kind == 'FUNC_DEF':
        _, ret, name, params, body = node
        param_nodes = [wrap(f'PARAM: {pt} {pn}') for pt, pn in params]
        return {'label': f'FUNC: {ret} {name}',
                'children': param_nodes + stmts(body)}
    if kind == 'DECL':
        _, name, expr, *rest = node
        dtype = rest[0] if rest else 'int'
        return wrap(f'DECL: {dtype} {name}', expr_node(expr))
    if kind == 'MULTI_DECL':
        _, dtype, pairs = node
        children = [wrap(f'DECL: {dtype} {n}', expr_node(e)) for n, e in pairs]
        return {'label': f'MULTI_DECL: {dtype}', 'children': children}
    if kind == 'ARRAY_DECL':
        _, dtype, name, size, init, *_ = node
        return wrap(f'ARRAY_DECL: {dtype} {name}', expr_node(size))
    if kind == 'ASSIGN':
        _, name, expr, *_ = node
        return wrap(f'ASSIGN: {name}', expr_node(expr))
    if kind == 'ARRAY_ASSIGN':
        _, name, idx, val, *_ = node
        return wrap(f'ARRAY_ASSIGN: {name}', expr_node(idx), expr_node(val))
    if kind == 'COMPOUND_ASSIGN':
        _, op, name, expr, *_ = node
        return wrap(f'COMPOUND {op}=: {name}', expr_node(expr))
    if kind == 'INCR':
        _, op, name, post, *_ = node
        return wrap(f'{"POST" if post else "PRE"}{op}: {name}')
    if kind == 'IF':
        _, cond, then_body, else_body = node
        then_node = {'label': 'THEN', 'children': stmts(then_body)}
        else_node = {'label': 'ELSE', 'children': stmts(else_body)} if else_body else None
        return wrap('IF', expr_node(cond), then_node, else_node)
    if kind == 'FOR':
        _, init, cond, update, body = node
        return {'label': 'FOR', 'children': [
            wrap('INIT', stmt_node(init)),
            wrap('COND', expr_node(cond)),
            wrap('UPDATE', stmt_node(update)),
            {'label': 'BODY', 'children': stmts(body)},
        ]}
    if kind == 'WHILE':
        _, cond, body = node
        return wrap('WHILE', expr_node(cond),
                    {'label': 'BODY', 'children': stmts(body)})
    if kind == 'DO_WHILE':
        _, body, cond = node
        return wrap('DO_WHILE',
                    {'label': 'BODY', 'children': stmts(body)},
                    expr_node(cond))
    if kind == 'SWITCH':
        _, expr, cases, default = node
        case_nodes = [{'label': 'CASE', 'children': [expr_node(cv)] + stmts(cs)}
                      for cv, cs in cases]
        default_node = {'label': 'DEFAULT', 'children': stmts(default)} if default else None
        return {'label': 'SWITCH', 'children': [expr_node(expr)] + case_nodes +
                ([default_node] if default_node else [])}
    if kind == 'RETURN':
        return wrap('RETURN', expr_node(node[1]))
    if kind == 'PRINT':
        return wrap('PRINT', expr_node(node[1]))
    if kind == 'PRINTF':
        return {'label': 'PRINTF', 'children': [expr_node(a) for a in node[1]]}
    if kind == 'SCANF':
        return {'label': 'SCANF', 'children': [wrap(f'&{v}') for v in node[1]]}
    if kind == 'CALL_STMT':
        _, name, args = node
        return {'label': f'CALL: {name}', 'children': [expr_node(a) for a in args]}
    if kind in ('BREAK',):
        return wrap('BREAK')
    if kind in ('CONTINUE',):
        return wrap('CONTINUE')
    return wrap(str(node))


class CompilerError(Exception):
    """Base class for compiler errors"""
    pass


class LexerError(CompilerError):
    """Lexical analysis error"""
    pass


class ParserError(CompilerError):
    """Syntax error"""
    pass


class SemanticError(CompilerError):
    """Semantic error"""
    pass


def compile_source(source_code, verbose=False):
    """
    Compile mini-C source code through all 6 phases.
    Returns dict with results or errors.
    """
    result = {
        'success': False,
        'phase': None,
        'error': None,
        'tokens': None,
        'ast': None,
        'symbol_table': None,
        'ir': None,
        'optimized_ir': None,
        'assembly': None
    }

    try:
        # Phase 1: Lexical Analysis
        if verbose:
            print('▶ Phase 1: Lexical Analysis...')
        result['phase'] = 1
        tokens = tokenize(source_code)
        result['tokens'] = tokens[:-1]  # exclude EOF
        if verbose:
            print(f'  ✓ Generated {len(tokens) - 1} tokens')

        # Phase 2: Syntax Analysis
        if verbose:
            print('▶ Phase 2: Syntax Analysis...')
        result['phase'] = 2
        ast = Parser(tokens).parse()
        result['ast'] = ast
        if verbose:
            print(f'  ✓ Generated AST')

        # Phase 3: Semantic Analysis
        if verbose:
            print('▶ Phase 3: Semantic Analysis...')
        result['phase'] = 3
        sem = SemanticAnalyzer()
        sem.analyze(ast)
        
        if sem.errors:
            raise SemanticError('\n  '.join(sem.errors))
        
        result['symbol_table'] = sem.symbol_table
        if verbose:
            print(f'  ✓ Symbol table: {len(sem.symbol_table)} variable(s)')

        # Phase 4: Intermediate Code Generation
        if verbose:
            print('▶ Phase 4: Intermediate Code Generation...')
        result['phase'] = 4
        ir = IRGenerator()
        ir.generate(ast)
        result['ir'] = ir.code
        if verbose:
            print(f'  ✓ Generated {len(ir.code)} TAC instructions')

        # Phase 5: Code Optimization
        if verbose:
            print('▶ Phase 5: Code Optimization...')
        result['phase'] = 5
        opt_ir = optimize(ir.code)
        result['optimized_ir'] = opt_ir
        if verbose:
            folded = sum(1 for l in opt_ir if '; folded' in l)
            prop = sum(1 for l in opt_ir if '; propagated' in l)
            print(f'  ✓ Applied {folded} constant folds, {prop} propagations')

        # Phase 6: Code Generation
        if verbose:
            print('▶ Phase 6: Code Generation...')
        result['phase'] = 6
        asm = code_gen(opt_ir)
        result['assembly'] = asm
        if verbose:
            print(f'  ✓ Generated {len(asm)} assembly lines')

        result['success'] = True
        return result

    except SyntaxError as e:
        result['error'] = f'SYNTAX ERROR (Phase {result["phase"]}): {str(e)}'
        return result
    except SemanticError as e:
        result['error'] = f'SEMANTIC ERROR: {str(e)}'
        return result
    except Exception as e:
        result['error'] = f'ERROR (Phase {result["phase"]}): {str(e)}'
        return result


def compile_file(filepath, verbose=False, output_asm=None):
    """Compile a .c file"""
    try:
        with open(filepath, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f'❌ File not found: {filepath}')
        return False
    except IOError as e:
        print(f'❌ Error reading file: {e}')
        return False

    result = compile_source(source_code, verbose=verbose)

    # Print results
    print('\n' + '=' * 60)
    print(f'  EveCompiler — Compilation Report')
    print('=' * 60)

    if result['success']:
        print('\n✅ COMPILATION SUCCESSFUL!\n')
        
        if result['symbol_table']:
            print('📊 Symbol Table:')
            for name, typ in result['symbol_table'].items():
                print(f'  {name:<15} : {typ}')
        
        print(f'\n📈 Compilation Statistics:')
        print(f'  Tokens:        {len(result["tokens"])}')
        print(f'  TAC lines:     {len(result["ir"])}')
        print(f'  Assembly:      {len(result["assembly"])}')
        
        if output_asm:
            with open(output_asm, 'w') as f:
                for line in result['assembly']:
                    f.write(line + '\n')
            print(f'\n💾 Assembly saved to: {output_asm}')
        else:
            print('\n🔧 Generated Assembly:')
            for line in result['assembly']:
                print(f'  {line}')
        
        return True
    else:
        print(f'\n❌ COMPILATION FAILED\n')
        print(f'⚠️  {result["error"]}\n')
        return False


def main():
    if len(sys.argv) < 2:
        print('Usage: python cli.py <source.c> [--output <output.asm>] [--verbose]')
        print('\nExample:')
        print('  python cli.py sample.c')
        print('  python cli.py sample.c --output output.asm --verbose')
        sys.exit(1)

    filepath = sys.argv[1]
    output_asm = None
    verbose = '--verbose' in sys.argv

    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_asm = sys.argv[idx + 1]

    success = compile_file(filepath, verbose=verbose, output_asm=output_asm)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
