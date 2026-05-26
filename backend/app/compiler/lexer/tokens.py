"""Token type definitions for the C++ subset compiler."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TT(Enum):
    # Literals
    INT_LIT = auto()
    FLOAT_LIT = auto()
    CHAR_LIT = auto()
    STRING_LIT = auto()
    BOOL_LIT = auto()
    # Identifiers / keywords
    IDENT = auto()
    KEYWORD = auto()
    TYPE = auto()
    # Arithmetic
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); PERCENT = auto()
    INC = auto(); DEC = auto()
    # Comparison
    EQ = auto(); NEQ = auto(); LT = auto(); GT = auto(); LTE = auto(); GTE = auto()
    # Logical / bitwise
    AND = auto(); OR = auto(); NOT = auto()
    SHL = auto(); SHR = auto()
    # Assignment
    ASSIGN = auto()
    PLUS_ASSIGN = auto(); MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto(); SLASH_ASSIGN = auto()
    # Delimiters
    LPAREN = auto(); RPAREN = auto()
    LBRACE = auto(); RBRACE = auto()
    LBRACK = auto(); RBRACK = auto()
    SEMI = auto(); COMMA = auto()
    COLON = auto(); SCOPE = auto()
    # Preprocessor (consumed but tracked)
    HASH = auto()
    # End
    EOF = auto()


# C++ type keywords (subset)
TYPE_KEYWORDS = {"int", "float", "double", "char", "bool", "void", "string", "long", "short"}

# Reserved keywords (subset)
KEYWORDS = {
    "if", "else", "while", "for", "do", "return", "break", "continue",
    "true", "false", "void", "class", "struct", "public", "private", "protected",
    "const", "static", "using", "namespace", "include", "std", "cout", "cin",
    "endl", "new", "delete", "this", "nullptr", "auto", "switch", "case", "default",
}


@dataclass
class Token:
    type: TT
    lexeme: str
    value: Any = None
    line: int = 1
    col: int = 1

    def to_dict(self) -> dict:
        return {
            "type": self.type.name,
            "lexeme": self.lexeme,
            "value": self.value,
            "line": self.line,
            "col": self.col,
        }
