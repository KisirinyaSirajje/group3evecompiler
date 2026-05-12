# EveCompiler IDE — Quick Start Guide

## 🚀 Getting Started

### Option 1: Use the Setup Script (Easiest)
```bash
cd /Users/macbook/Desktop/evecompiler_ide
chmod +x start.sh
./start.sh
```

### Option 2: Manual Setup

#### First Time Setup
```bash
cd /Users/macbook/Desktop/evecompiler_ide

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install flask
```

#### Run CLI (Command-line Compiler)
```bash
# Activate virtual environment first
source venv/bin/activate

# Compile a file
python cli.py sample_programs/simple.c

# With verbose output
python cli.py sample_programs/simple.c --verbose

# Save assembly output
python cli.py sample_programs/simple.c --output output.asm
```

#### Run Web UI (Interactive IDE)
```bash
# Activate virtual environment first
source venv/bin/activate

# Start the server
python app.py

# Open http://localhost:5000 in your browser
# Press Ctrl+C to stop
```

---

## 📝 Writing Your Own Code

Create a new `.c` file:
```bash
cat > my_program.c << 'EOF'
int x = 5;
int y = 10;
int z = x + y;
if (z > 15) {
    print(z);
} else {
    print(x);
}
EOF
```

Compile it:
```bash
source venv/bin/activate
python cli.py my_program.c --verbose
```

---

## 🐛 Error Examples

### Example 1: Undeclared Variable
**File:** `error1.c`
```c
int x = 5;
print(y);
```

**Result:**
```
❌ COMPILATION FAILED
⚠️  SEMANTIC ERROR: Undeclared variable 'y'
```

### Example 2: Duplicate Declaration
**File:** `error2.c`
```c
int x = 5;
int x = 10;
```

**Result:**
```
❌ COMPILATION FAILED
⚠️  SEMANTIC ERROR: Variable 'x' already declared
```

### Example 3: Syntax Error
**File:** `error3.c`
```c
int x 5;
```

**Result:**
```
❌ COMPILATION FAILED
⚠️  SYNTAX ERROR: Expected 'ASSIGN', got 'NUMBER'
```

---

## 🎯 Sample Programs

All samples are in `sample_programs/`:

### `simple.c` - Basic if/else with arithmetic
```bash
python cli.py sample_programs/simple.c
```

### `loop.c` - While loop counter
```bash
python cli.py sample_programs/loop.c --verbose
```

### `arithmetic.c` - Arithmetic operations
```bash
python cli.py sample_programs/arithmetic.c --output arith.asm
```

### `nested_loops.c` - Nested loops
```bash
python cli.py sample_programs/nested_loops.c --verbose
```

---

## 🖥️ Web UI Features

Once the server is running (`python app.py`):

1. **Write Code** - Paste or type mini-C code in the editor
2. **Compile** - Click "🚀 Compile" button
3. **View Results** - Click tabs to see:
   - 📊 Compilation statistics
   - 🔤 Token list
   - 📋 Symbol table
   - ⚙️ Optimized IR code
   - 🤖 Generated assembly
4. **Load Samples** - Click "📚 Load Sample" to try examples
5. **Clear** - Reset code with "🗑️ Clear" button

---

## 📊 What Each Phase Does

| Phase | Input | Output | Example |
|-------|-------|--------|---------|
| 1 | Source code | Tokens | `int`, `x`, `=`, `5`, `;` |
| 2 | Tokens | AST | `('DECL', 'x', ('NUM', 5))` |
| 3 | AST | Symbol Table | `{x: int}` |
| 4 | AST | TAC | `x = 5`, `print x` |
| 5 | TAC | Optimized TAC | Constant folding & propagation |
| 6 | Opt TAC | Assembly | `LOAD 5`, `STORE x` |

---

## 💡 Tips

- **Deactivate venv** when done: `deactivate`
- **Re-enter venv**: `source venv/bin/activate`
- **Check Python version**: `python3 --version`
- **Check Flask installed**: `pip list | grep flask`
- **Kill stuck Flask server**: `lsof -ti:5000 | xargs kill -9`

---

## ❓ Troubleshooting

### "Flask not found"
```bash
source venv/bin/activate
pip install flask
```

### "Port 5000 already in use"
```bash
# Kill the process using port 5000
lsof -ti:5000 | xargs kill -9
# Then start app.py again
```

### Virtual environment not working
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install flask
```

---

## 📚 File Structure

```
evecompiler_ide/
├── cli.py                  ← Run this for CLI
├── app.py                  ← Run this for Web UI
├── compiler_phases/        ← All 6 phases
├── static/                 ← Web UI styling
├── templates/              ← Web UI HTML
├── sample_programs/        ← Example .c files
├── venv/                   ← Virtual environment (created by setup)
└── README.md
```

---

Enjoy your EveCompiler IDE! 🎉
