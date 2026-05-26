# C++ MiniCompiler — Full-Stack Compiler System

A teaching-grade compiler for a meaningful subset of **C++** with a modern
React + Monaco frontend and a FastAPI backend.

## Features

- **Lexer** — full C++ subset: `int float double char bool string void`,
  arithmetic / comparison / logical / bitwise shift ops, `++ -- += -= *= /=`,
  `//` and `/* */` comments, string/char literals, preprocessor lines.
- **Parser** — recursive-descent → typed AST (function decls, var decls,
  `if/else`, `while`, `for`, `return/break/continue`, expressions, calls,
  `cout << … << endl;`, `cin >> x;`).
- **Semantic analysis** — scoped symbol table, type compatibility &
  promotion, undefined-identifier checks, function arity/type checks,
  break/continue scope, return-type checks.
- **IR / Bytecode** — stack-based instructions (`LOAD_CONST`, `STORE`,
  `BINOP`, `JUMP_IF_FALSE`, `CALL`, `PRINT`, …).
- **VM** — executes the bytecode so `/run` returns real program output.
- **REST API** — `POST /compile`, `POST /run`, `GET /health`.
- **React + Monaco UI** — light blue VS Code–style theme, C++ syntax
  highlighting, tabbed panels for Tokens / AST / Symbols / IR / Errors / Output.
- **Tests** — `pytest` unit tests for lexer + end-to-end compile/run.
- **Docker** — one-command spin-up via `docker compose up --build`.

## Architecture

```
┌──────────────┐  HTTP/JSON   ┌─────────────────────────────────────────────┐
│ React (5173) │ ───────────► │ FastAPI (8000)                              │
│  Monaco UI   │              │  /compile  /run  /health                    │
└──────────────┘              │   │                                         │
                              │   ▼                                         │
                              │  Compiler facade                            │
                              │   ├── lexer/      (tokens.py, lexer.py)     │
                              │   ├── parser/     (parser.py)               │
                              │   ├── ast/        (nodes.py — Visitor)      │
                              │   ├── semantic/   (analyzer.py)             │
                              │   ├── symbol_table/(table.py — scoped)      │
                              │   ├── codegen/    (generator.py — IR)       │
                              │   └── runtime/    (vm.py — stack VM)        │
                              └─────────────────────────────────────────────┘
```

Design patterns used: **Facade** (`Compiler`), **Visitor** (semantic +
codegen dispatch via `type(node).__name__`), **Factory** (token construction
in the lexer).

## Project structure

```
backend/
  app/
    main.py                 FastAPI app
    api/routes.py           /compile, /run, /health
    models/schemas.py       Pydantic DTOs
    compiler/
      compiler.py           Facade
      lexer/                tokens.py, lexer.py
      parser/               parser.py
      ast/                  nodes.py
      semantic/             analyzer.py
      symbol_table/         table.py
      codegen/              generator.py
      runtime/              vm.py
  tests/                    pytest tests
  Dockerfile
  requirements.txt
frontend/
  src/
    App.jsx                 Main UI
    components/             TokenTable, AstTree, SymbolTable
    services/api.js         Compile/Run REST calls
    styles/app.css          Light blue theme
  vite.config.js            Dev proxy → backend
  Dockerfile
  package.json
docker-compose.yml
```

## Running locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```
The Vite dev server proxies `/api/*` → `http://localhost:8000`.

### Tests
```bash
cd backend && pytest -q
```

### Docker (everything)
```bash
docker compose up --build
# Frontend: http://localhost:5173    Backend: http://localhost:8000
```

## REST API

### `POST /compile`
```json
{ "source_code": "int main(){ return 0; }" }
```
Returns `{ success, tokens, ast, symbol_table, bytecode, bytecode_text, errors }`.

### `POST /run`
```json
{ "source_code": "…", "stdin": "" }
```
Returns `{ success, stdout, errors }`.

## Supported C++ subset

| Category   | Supported                                                        |
|------------|------------------------------------------------------------------|
| Types      | `int float double char bool string void long short`              |
| Control    | `if / else`, `while`, `for`, `break`, `continue`, `return`       |
| Functions  | Declarations with params, recursion, calls                       |
| Operators  | `+ - * / %`, `== != < > <= >=`, `&& || !`, `++/--` (pre/post), compound assign |
| I/O        | `std::cout << … << endl;`, `std::cin >> x;` (uses `/run` stdin)  |
| Preproc    | `#include` / `using namespace std;` (parsed, ignored)            |

## Sample

```cpp
#include <iostream>
using namespace std;
int add(int a, int b) { return a + b; }
int main() {
    int z = add(10, 32);
    if (z > 40) cout << "big: " << z << endl;
    return 0;
}
```
