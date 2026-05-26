"""Semantic analysis: type & scope checking using the Visitor pattern."""
from __future__ import annotations
from typing import List, Optional
from ..ast.nodes import (
    Program, FuncDecl, Param, VarDecl, Block, If, While, For, Return, Break,
    Continue, ExprStmt, BinaryOp, UnaryOp, Assign, Call, Identifier, IntLit,
    FloatLit, BoolLit, CharLit, StringLit, CoutStmt, CinStmt, Node,
)
from ..symbol_table import SymbolTable, Symbol


NUMERIC = {"int", "float", "double", "long", "short", "char"}
INTEGRAL = {"int", "long", "short", "char", "bool"}


def _promote(a: str, b: str) -> str:
    order = ["bool", "char", "short", "int", "long", "float", "double"]
    return order[max(order.index(a), order.index(b))] if a in order and b in order else a


class SemanticError(Exception):
    def __init__(self, msg: str, line: int):
        super().__init__(f"[Semantic error] line {line}: {msg}")
        self.line = line


class SemanticAnalyzer:
    """Walks the AST, fills the symbol table, returns a list of errors."""

    def __init__(self):
        self.table = SymbolTable()
        self.errors: List[str] = []
        self.current_func_return: Optional[str] = None
        self.loop_depth = 0

    # ── public ────────────────────────────────────────────
    def analyze(self, program: Program):
        # pre-pass: register all functions (so order doesn't matter)
        for d in program.declarations:
            if isinstance(d, FuncDecl):
                self.table.define(Symbol(d.name, "func", d.return_type, "global", d.line,
                                         extra={"params": [(p.param_type, p.name) for p in d.params]}))
        for d in program.declarations:
            self.visit(d)
        return self.errors

    # ── dispatcher ────────────────────────────────────────
    def visit(self, n: Node):
        return getattr(self, f"visit_{type(n).__name__}", self.generic)(n)

    def generic(self, n: Node):
        return "void"

    # ── declarations ──────────────────────────────────────
    def visit_FuncDecl(self, n: FuncDecl):
        self.table.enter(n.name)
        for p in n.params:
            if not self.table.define(Symbol(p.name, "param", p.param_type, n.name, p.line)):
                self.errors.append(f"[Semantic error] line {p.line}: duplicate parameter '{p.name}'")
        prev = self.current_func_return
        self.current_func_return = n.return_type
        if n.body:
            for s in n.body.statements:
                self.visit(s)
        self.current_func_return = prev
        self.table.leave()

    def visit_VarDecl(self, n: VarDecl):
        scope_name = self.table.current.name
        if not self.table.define(Symbol(n.name, "var", n.var_type, scope_name, n.line)):
            self.errors.append(f"[Semantic error] line {n.line}: variable '{n.name}' already declared in scope")
        if n.init is not None:
            it = self.visit(n.init)
            if not self._assignable(n.var_type, it):
                self.errors.append(f"[Semantic error] line {n.line}: cannot initialize '{n.var_type}' with '{it}'")

    # ── statements ────────────────────────────────────────
    def visit_Block(self, n: Block):
        self.table.enter("block")
        for s in n.statements:
            self.visit(s)
        self.table.leave()

    def visit_If(self, n: If):
        ct = self.visit(n.cond)
        if ct not in ("bool", "int", "char", "short", "long"):
            self.errors.append(f"[Semantic error] line {n.line}: if condition must be boolean/integral, got '{ct}'")
        self.visit(n.then_branch)
        if n.else_branch is not None:
            self.visit(n.else_branch)

    def visit_While(self, n: While):
        self.visit(n.cond)
        self.loop_depth += 1
        self.visit(n.body)
        self.loop_depth -= 1

    def visit_For(self, n: For):
        self.table.enter("for")
        if n.init: self.visit(n.init)
        if n.cond: self.visit(n.cond)
        if n.update: self.visit(n.update)
        self.loop_depth += 1
        self.visit(n.body)
        self.loop_depth -= 1
        self.table.leave()

    def visit_Return(self, n: Return):
        if self.current_func_return is None:
            self.errors.append(f"[Semantic error] line {n.line}: return outside function")
            return
        if n.value is None:
            if self.current_func_return != "void":
                self.errors.append(f"[Semantic error] line {n.line}: function must return '{self.current_func_return}'")
            return
        vt = self.visit(n.value)
        if not self._assignable(self.current_func_return, vt):
            self.errors.append(f"[Semantic error] line {n.line}: return type '{vt}' incompatible with '{self.current_func_return}'")

    def visit_Break(self, n: Break):
        if self.loop_depth == 0:
            self.errors.append(f"[Semantic error] line {n.line}: 'break' outside loop")

    def visit_Continue(self, n: Continue):
        if self.loop_depth == 0:
            self.errors.append(f"[Semantic error] line {n.line}: 'continue' outside loop")

    def visit_ExprStmt(self, n: ExprStmt):
        if n.expr is not None:
            self.visit(n.expr)

    def visit_CoutStmt(self, n: CoutStmt):
        for p in n.parts:
            self.visit(p)

    def visit_CinStmt(self, n: CinStmt):
        for name in n.targets:
            sym = self.table.resolve(name)
            if sym is None:
                self.errors.append(f"[Semantic error] line {n.line}: undefined variable '{name}'")

    # ── expressions ───────────────────────────────────────
    def visit_IntLit(self, n): return "int"
    def visit_FloatLit(self, n): return "double"
    def visit_BoolLit(self, n): return "bool"
    def visit_CharLit(self, n): return "char"
    def visit_StringLit(self, n): return "string"

    def visit_Identifier(self, n: Identifier):
        sym = self.table.resolve(n.name)
        if sym is None:
            self.errors.append(f"[Semantic error] line {n.line}: undefined identifier '{n.name}'")
            return "int"
        return sym.type

    def visit_Assign(self, n: Assign):
        sym = self.table.resolve(n.target)
        if sym is None:
            self.errors.append(f"[Semantic error] line {n.line}: undefined variable '{n.target}'")
            return "int"
        vt = self.visit(n.value)
        if not self._assignable(sym.type, vt):
            self.errors.append(f"[Semantic error] line {n.line}: cannot assign '{vt}' to '{sym.type}'")
        return sym.type

    def visit_BinaryOp(self, n: BinaryOp):
        lt = self.visit(n.left)
        rt = self.visit(n.right)
        if n.op in ("&&", "||"): return "bool"
        if n.op in ("==", "!=", "<", ">", "<=", ">="): return "bool"
        if lt in NUMERIC and rt in NUMERIC:
            return _promote(lt, rt)
        if n.op == "+" and (lt == "string" or rt == "string"):
            return "string"
        self.errors.append(f"[Semantic error] line {n.line}: operator '{n.op}' invalid for '{lt}' and '{rt}'")
        return lt

    def visit_UnaryOp(self, n: UnaryOp):
        t = self.visit(n.operand)
        if n.op == "!": return "bool"
        return t

    def visit_Call(self, n: Call):
        sym = self.table.resolve(n.callee)
        if sym is None or sym.kind != "func":
            self.errors.append(f"[Semantic error] line {n.line}: undefined function '{n.callee}'")
            return "int"
        params = sym.extra.get("params", [])
        if len(params) != len(n.args):
            self.errors.append(f"[Semantic error] line {n.line}: '{n.callee}' expects {len(params)} args, got {len(n.args)}")
        for (pt, _), arg in zip(params, n.args):
            at = self.visit(arg)
            if not self._assignable(pt, at):
                self.errors.append(f"[Semantic error] line {n.line}: argument type '{at}' incompatible with '{pt}'")
        return sym.type

    # ── helpers ───────────────────────────────────────────
    @staticmethod
    def _assignable(target: str, source: str) -> bool:
        if target == source: return True
        if target in NUMERIC and source in NUMERIC: return True
        if target == "bool" and source in INTEGRAL: return True
        return False
