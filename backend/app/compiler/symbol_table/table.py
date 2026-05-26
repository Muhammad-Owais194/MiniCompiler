"""Scoped symbol table."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


@dataclass
class Symbol:
    name: str
    kind: str        # 'var' | 'func' | 'param'
    type: str
    scope: str
    line: int
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class Scope:
    def __init__(self, name: str, parent: Optional["Scope"] = None):
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, sym: Symbol) -> bool:
        if sym.name in self.symbols:
            return False
        self.symbols[sym.name] = sym
        return True

    def resolve(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        return None


class SymbolTable:
    """Tree of scopes with a flat view for reporting."""

    def __init__(self):
        self.global_scope = Scope("global")
        self.current = self.global_scope
        self._all: List[Symbol] = []

    def enter(self, name: str):
        self.current = Scope(name, self.current)

    def leave(self):
        assert self.current.parent is not None
        self.current = self.current.parent

    def define(self, sym: Symbol) -> bool:
        ok = self.current.define(sym)
        if ok:
            self._all.append(sym)
        return ok

    def resolve(self, name: str) -> Optional[Symbol]:
        return self.current.resolve(name)

    def all_symbols(self) -> List[dict]:
        return [s.to_dict() for s in self._all]
