# z3-pyodide

A pure-Python Z3 theorem prover package that works in the browser via [Pyodide](https://pyodide.org/). Provides a **z3-py compatible API** using the SMT-LIB2 text protocol, communicating with Z3 compiled to WebAssembly.

**[Live Demo](https://alcides.github.io/z3-pyodide/)**

## Quick Example

```python
from z3_pyodide import *

x, y = Ints('x y')
s = Solver()
s.add(x + y == 10)
s.add(x > 0, y > 0)
s.add(x > y)

if s.check() == sat:
    m = s.model()
    print(f"x = {m[x]}, y = {m[y]}")  # x = 9, y = 1
```

## Features

- **z3-py compatible API** — `Int`, `Real`, `Bool`, `BitVec`, `Array`, `Solver`, `Optimize`, `ForAll`, `Exists`, `Datatype`, and more
- **Pure Python** — zero dependencies, installable via `micropip` in Pyodide
- **Dual backend** — subprocess (CPython) and WebAssembly (Pyodide), auto-detected
- **SMT-LIB2 protocol** — generates SMT-LIB2 text, sends to Z3, parses results

### Supported theories

| Theory | Types | Operations |
|--------|-------|------------|
| **Integers** | `Int`, `IntVal` | `+`, `-`, `*`, `/`, `%`, comparisons |
| **Reals** | `Real`, `RealVal` | arithmetic, `ToReal`, `ToInt` |
| **Booleans** | `Bool`, `BoolVal` | `And`, `Or`, `Not`, `Implies`, `Xor` |
| **BitVectors** | `BitVec`, `BitVecVal` | bitwise ops, shifts, `Extract`, `Concat`, `ZeroExt`, `SignExt` |
| **Arrays** | `Array` | `Select`, `Store`, `K` (constant arrays) |
| **Datatypes** | `Datatype` | enums, records, recursive types, mutual recursion |
| **Quantifiers** | `ForAll`, `Exists` | with uninterpreted `Function` |
| **Optimization** | `Optimize` | `minimize`, `maximize` |

## Installation

### In Pyodide (browser)

```python
import micropip
await micropip.install('z3_pyodide')  # once published to PyPI
```

### Local development (CPython)

```bash
pip install z3-solver  # provides the Z3 binary
pip install -e .       # install z3_pyodide
```

## Running the example page locally

```bash
bash examples/setup.sh    # downloads Z3 WASM (~17 MB, one time)
python3 examples/server.py  # serves on http://localhost:8000
```

## Running tests

```bash
pip install z3-solver pytest
pytest tests/ -v
```

## Architecture

```
Python code  →  AST (ExprRef, BoolRef, ArithRef, ...)
                  ↓
             SMT-LIB2 text generation
                  ↓
             Backend (subprocess z3 or WASM z3)
                  ↓
             S-expression parser  →  Model extraction
```

The package builds a Python AST with operator overloading (`x + y == 10`), serializes it to SMT-LIB2 text, sends it to Z3 via either a local subprocess or a WASM Web Worker, and parses the results back into Python objects.

## License

MIT
