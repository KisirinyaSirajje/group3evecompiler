# 🔧 EveCompiler IDE

A complete **mini-C compiler** with **CLI** and **Web UI** interfaces, featuring full error detection and detailed compilation reports.

## Features

✅ **Full 6-Phase Compiler**
- Phase 1: Lexical Analysis (Tokenization)
- Phase 2: Syntax Analysis (Parsing → AST)
- Phase 3: Semantic Analysis (Type Checking, Symbol Table)
- Phase 4: Intermediate Code Generation (Three-Address Code)
- Phase 5: Code Optimization (Constant Folding & Propagation)
- Phase 6: Code Generation (Pseudo-Assembly)

✅ **Error Detection**
- Syntax Errors (parsing failures)
- Semantic Errors (undeclared variables, duplicate declarations)
- Detailed error messages with phase information

✅ **Multiple Interfaces**
1. **CLI** - Command-line compilation with detailed reporting
2. **Web UI** - Interactive IDE with live compilation and visualization

✅ **Supported mini-C Features**
- Variable declarations: `int x = value;`
- Arithmetic operations: `+`, `-`, `*`, `/`
- Relational operations: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Control flow: `if`/`else`, `while` loops
- I/O: `print()` function

---

## Installation

### Requirements
- Python 3.7+
- Flask (for web UI)

### Setup

```bash
# Navigate to the project directory
cd /Users/macbook/Desktop/evecompiler_ide

# Install dependencies (if needed)
pip install flask
```

---

## Usage

### CLI Mode (Command-line)

Compile a source file:
```bash
python cli.py sample_programs/simple.c
```

Compile with verbose output:
```bash
python cli.py sample_programs/simple.c --verbose
```

Save assembly output:
```bash
python cli.py sample_programs/simple.c --output output.asm
```

**Example output:**
```
============================================================
  EveCompiler — Compilation Report
============================================================

✅ COMPILATION SUCCESSFUL!

📊 Symbol Table:
  x              : int
  y              : int
  z              : int

📈 Compilation Statistics:
  Tokens:        16
  TAC lines:     8
  Assembly:      12

🔧 Generated Assembly:
  .data
      x        DW  0
      y        DW  0
      z        DW  0

  .code
      LOAD  5
      STORE x
      LOAD  10
      STORE y
      LOAD  x
      ADD   y
      STORE z
      HALT
```

### Web UI Mode

Start the web server:
```bash
python app.py
```

Then open your browser to:
```
http://localhost:5000
```

**Features:**
- 📝 Write or paste mini-C code
- 🚀 One-click compilation
- 📊 View compilation statistics
- 🔤 Token list visualization
- 📋 Symbol table display
- ⚙️ Optimized IR code view
- 🤖 Generated assembly view
- 📚 Load sample programs

---

## Sample Programs

Located in `sample_programs/`:

### `simple.c` - Basic if/else
```c
int x = 5;
int y = 10;
int z = x + y;
if (z > 10) {
    print(z);
} else {
    print(x);
}
```

### `loop.c` - While loop
```c
int count = 0;
int limit = 5;
while (count < limit) {
    print(count);
    count = count + 1;
}
```

### `arithmetic.c` - Arithmetic operations
```c
int a = 10;
int b = 20;
int sum = a + b;
int product = a * b;
```

### `nested_loops.c` - Nested loops
```c
int i = 1;
while (i <= 3) {
    int j = 1;
    while (j <= 3) {
        print(i);
        j = j + 1;
    }
    i = i + 1;
}
```

---

## Error Examples

### Syntax Error (undeclared variable)
```c
int x = 5;
print(y);  // ERROR: Undeclared variable 'y'
```

Output:
```
❌ COMPILATION FAILED

⚠️  SEMANTIC ERROR: Undeclared variable 'y'
```

### Semantic Error (duplicate declaration)
```c
int x = 5;
int x = 10;  // ERROR: Variable 'x' already declared
```

Output:
```
❌ COMPILATION FAILED

⚠️  SEMANTIC ERROR: Variable 'x' already declared
```

---

## Compiler Architecture

### Input Flow
```
Source Code (.c)
    ↓
[Phase 1: Lexer] → Tokens
    ↓
[Phase 2: Parser] → Abstract Syntax Tree (AST)
    ↓
[Phase 3: Semantic] → Symbol Table + Error Check
    ↓
[Phase 4: IRGen] → Three-Address Code (TAC)
    ↓
[Phase 5: Optimizer] → Optimized TAC
    ↓
[Phase 6: CodeGen] → Pseudo-Assembly
    ↓
Output (.asm or Display)
```

### Key Optimizations
- **Constant Folding**: `5 + 10` → `15`
- **Constant Propagation**: Replace variables with known constants
- **Dead Code Elimination**: Remove unused instructions

---

## Project Structure

```
evecompiler_ide/
├── compiler_phases/           # Compiler implementation
│   ├── __init__.py
│   ├── phase1_lexer.py       # Tokenization
│   ├── phase2_parser.py      # Syntax parsing
│   ├── phase3_semantic.py    # Type checking
│   ├── phase4_irgen.py       # IR generation
│   ├── phase5_optimizer.py   # Optimization
│   └── phase6_codegen.py     # Assembly generation
├── cli.py                     # Command-line interface
├── app.py                     # Flask web server
├── templates/
│   └── index.html            # Web UI
├── static/
│   ├── style.css             # UI styling
│   └── script.js             # Frontend logic
├── sample_programs/          # Example .c files
│   ├── simple.c
│   ├── loop.c
│   ├── arithmetic.c
│   └── nested_loops.c
└── README.md
```

---

## API Endpoints (Web UI)

### POST `/api/compile`
Compile source code.

**Request:**
```json
{
    "code": "int x = 5; print(x);"
}
```

**Response (Success):**
```json
{
    "success": true,
    "phase": 6,
    "statistics": {
        "tokens": 9,
        "ir_lines": 2,
        "assembly_lines": 5
    },
    "symbol_table": {"x": "int"},
    "tokens": [
        {"type": "KEYWORD", "value": "int"},
        {"type": "ID", "value": "x"},
        ...
    ],
    "optimized_ir": ["x = 5", "print x"],
    "assembly": [".data", "x DW 0", ".code", ...]
}
```

**Response (Error):**
```json
{
    "success": false,
    "phase": 2,
    "error": "SYNTAX ERROR (Phase 2): [Parser] Expected 'SEMI', got 'EOF'"
}
```

### GET `/api/samples`
Get available sample programs.

**Response:**
```json
{
    "simple": "int x = 5; ...",
    "loop": "int count = 0; ...",
    ...
}
```

---

## Development

### Adding New Keywords
Edit `compiler_phases/phase1_lexer.py`:
```python
TOKEN_SPEC = [
    ('KEYWORD',  r'\b(int|if|else|while|print|return|float|char)\b'),
    ...
]
```

### Adding New Language Features
1. Update lexer with new token types
2. Update parser with new grammar rules
3. Update semantic analyzer with type checking
4. Update IR generator with code generation
5. Update optimizer with optimization rules
6. Update code generator with assembly output

---

## License

Educational project - Free to use and modify

---

## Author

EveCompiler Development Team

Created as a comprehensive compiler implementation with error detection and user-friendly interfaces.
