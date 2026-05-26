"""AST node definitions for the C++ subset."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any, Union


# ── Base ────────────────────────────────────────────────────
@dataclass
class Node:
    line: int = 0

    def to_dict(self) -> dict:
        d = {"node": type(self).__name__}
        for k, v in self.__dict__.items():
            if k == "line":
                continue
            d[k] = _serialize(v)
        d["line"] = self.line
        return d


def _serialize(v: Any) -> Any:
    if isinstance(v, Node):
        return v.to_dict()
    if isinstance(v, list):
        return [_serialize(i) for i in v]
    return v


# ── Expressions ─────────────────────────────────────────────
@dataclass
class IntLit(Node):
    value: int = 0

@dataclass
class FloatLit(Node):
    value: float = 0.0

@dataclass
class BoolLit(Node):
    value: bool = False

@dataclass
class CharLit(Node):
    value: str = ""

@dataclass
class StringLit(Node):
    value: str = ""

@dataclass
class Identifier(Node):
    name: str = ""

@dataclass
class BinaryOp(Node):
    op: str = ""
    left: Optional[Node] = None
    right: Optional[Node] = None

@dataclass
class UnaryOp(Node):
    op: str = ""
    operand: Optional[Node] = None

@dataclass
class Assign(Node):
    target: str = ""
    op: str = "="
    value: Optional[Node] = None

@dataclass
class Call(Node):
    callee: str = ""
    args: List[Node] = field(default_factory=list)

@dataclass
class CoutStmt(Node):
    """std::cout << a << b << endl;"""
    parts: List[Node] = field(default_factory=list)

@dataclass
class CinStmt(Node):
    targets: List[str] = field(default_factory=list)


# ── Statements ──────────────────────────────────────────────
@dataclass
class VarDecl(Node):
    var_type: str = ""
    name: str = ""
    init: Optional[Node] = None

@dataclass
class Block(Node):
    statements: List[Node] = field(default_factory=list)

@dataclass
class If(Node):
    cond: Optional[Node] = None
    then_branch: Optional[Node] = None
    else_branch: Optional[Node] = None

@dataclass
class While(Node):
    cond: Optional[Node] = None
    body: Optional[Node] = None

@dataclass
class For(Node):
    init: Optional[Node] = None
    cond: Optional[Node] = None
    update: Optional[Node] = None
    body: Optional[Node] = None

@dataclass
class Return(Node):
    value: Optional[Node] = None

@dataclass
class Break(Node): pass

@dataclass
class Continue(Node): pass

@dataclass
class ExprStmt(Node):
    expr: Optional[Node] = None


# ── Declarations ────────────────────────────────────────────
@dataclass
class Param(Node):
    param_type: str = ""
    name: str = ""

@dataclass
class FuncDecl(Node):
    return_type: str = ""
    name: str = ""
    params: List[Param] = field(default_factory=list)
    body: Optional[Block] = None

@dataclass
class Program(Node):
    declarations: List[Node] = field(default_factory=list)
