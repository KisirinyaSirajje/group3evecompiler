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
