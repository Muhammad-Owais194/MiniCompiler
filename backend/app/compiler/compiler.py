"""High-level compiler facade — orchestrates all phases."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .lexer import Lexer, LexerError
from .parser import Parser, ParseError
from .semantic import SemanticAnalyzer
from .codegen import CodeGenerator, format_bytecode, bytecode_to_dict
from .runtime import VM, VMError


@dataclass
class CompileResult:
    success: bool
    tokens: list = field(default_factory=list)
    ast: Optional[dict] = None
    symbol_table: list = field(default_factory=list)
    bytecode_text: str = ""
    bytecode: list = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    _functions: dict = field(default_factory=dict)


class Compiler:
    """Single entry point — call .compile(source)."""

    def compile(self, source: str) -> CompileResult:
        result = CompileResult(success=False)
        try:
            tokens = Lexer(source).tokenize()
        except LexerError as e:
            result.errors.append(str(e))
            return result
        result.tokens = [t.to_dict() for t in tokens]

        try:
            ast = Parser(tokens).parse()
        except ParseError as e:
            result.errors.append(str(e))
            return result
        result.ast = ast.to_dict()

        analyzer = SemanticAnalyzer()
        sem_errors = analyzer.analyze(ast)
        result.symbol_table = analyzer.table.all_symbols()
        result.errors.extend(sem_errors)
        if sem_errors:
            return result

        gen = CodeGenerator()
        funcs = gen.generate(ast)
        result.bytecode_text = format_bytecode(funcs)
        result.bytecode = bytecode_to_dict(funcs)
        result._functions = funcs
        result.success = True
        return result

    def run(self, source: str, stdin: str = "") -> dict:
        cr = self.compile(source)
        if not cr.success:
            return {"success": False, "errors": cr.errors, "stdout": ""}
        try:
            out = VM(cr._functions, stdin=stdin).run("main")
            return {"success": True, "errors": [], "stdout": out}
        except VMError as e:
            return {"success": False, "errors": [f"[Runtime error] {e}"], "stdout": ""}
