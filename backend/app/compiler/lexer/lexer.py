"""Hand-written lexer for a meaningful subset of C++."""
from __future__ import annotations
from typing import List
from .tokens import Token, TT, KEYWORDS, TYPE_KEYWORDS


class LexerError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"[Lex error] line {line}:{col}: {msg}")
        self.line = line
        self.col = col


class Lexer:
    """Converts a C++ source string into a stream of tokens."""

    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    # -- helpers --
    def _peek(self, offset: int = 0) -> str:
        p = self.pos + offset
        return self.src[p] if p < len(self.src) else "\0"

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def _add(self, t: TT, lex: str, value=None, line=None, col=None):
        self.tokens.append(Token(t, lex, value, line or self.line, col or self.col))

    # -- main --
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.src):
            self._skip_ws_and_comments()
            if self.pos >= len(self.src):
                break
            self._scan_token()
        self._add(TT.EOF, "")
        return self.tokens

    def _skip_ws_and_comments(self):
        while self.pos < len(self.src):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "/" and self._peek(1) == "/":
                while self.pos < len(self.src) and self._peek() != "\n":
                    self._advance()
            elif ch == "/" and self._peek(1) == "*":
                self._advance(); self._advance()
                while self.pos < len(self.src) and not (self._peek() == "*" and self._peek(1) == "/"):
                    self._advance()
                if self.pos < len(self.src):
                    self._advance(); self._advance()
            else:
                break

    def _scan_token(self):
        line, col = self.line, self.col
        ch = self._peek()

        # Preprocessor directives: consume whole line
        if ch == "#":
            while self.pos < len(self.src) and self._peek() != "\n":
                self._advance()
            return

        if ch.isalpha() or ch == "_":
            self._scan_identifier(line, col)
            return
        if ch.isdigit():
            self._scan_number(line, col)
            return
        if ch == '"':
            self._scan_string(line, col)
            return
        if ch == "'":
            self._scan_char(line, col)
            return

        self._advance()
        single = {
            "(": TT.LPAREN, ")": TT.RPAREN,
            "{": TT.LBRACE, "}": TT.RBRACE,
            "[": TT.LBRACK, "]": TT.RBRACK,
            ";": TT.SEMI, ",": TT.COMMA,
            "%": TT.PERCENT,
        }
        if ch in single:
            self._add(single[ch], ch, line=line, col=col)
            return
        if ch == "+":
            if self._match("+"): self._add(TT.INC, "++", line=line, col=col)
            elif self._match("="): self._add(TT.PLUS_ASSIGN, "+=", line=line, col=col)
            else: self._add(TT.PLUS, "+", line=line, col=col)
            return
        if ch == "-":
            if self._match("-"): self._add(TT.DEC, "--", line=line, col=col)
            elif self._match("="): self._add(TT.MINUS_ASSIGN, "-=", line=line, col=col)
            else: self._add(TT.MINUS, "-", line=line, col=col)
            return
        if ch == "*":
            if self._match("="): self._add(TT.STAR_ASSIGN, "*=", line=line, col=col)
            else: self._add(TT.STAR, "*", line=line, col=col)
            return
        if ch == "/":
            if self._match("="): self._add(TT.SLASH_ASSIGN, "/=", line=line, col=col)
            else: self._add(TT.SLASH, "/", line=line, col=col)
            return
        if ch == "=":
            if self._match("="): self._add(TT.EQ, "==", line=line, col=col)
            else: self._add(TT.ASSIGN, "=", line=line, col=col)
            return
        if ch == "!":
            if self._match("="): self._add(TT.NEQ, "!=", line=line, col=col)
            else: self._add(TT.NOT, "!", line=line, col=col)
            return
        if ch == "<":
            if self._match("="): self._add(TT.LTE, "<=", line=line, col=col)
            elif self._match("<"): self._add(TT.SHL, "<<", line=line, col=col)
            else: self._add(TT.LT, "<", line=line, col=col)
            return
        if ch == ">":
            if self._match("="): self._add(TT.GTE, ">=", line=line, col=col)
            elif self._match(">"): self._add(TT.SHR, ">>", line=line, col=col)
            else: self._add(TT.GT, ">", line=line, col=col)
            return
        if ch == "&" and self._match("&"):
            self._add(TT.AND, "&&", line=line, col=col); return
        if ch == "|" and self._match("|"):
            self._add(TT.OR, "||", line=line, col=col); return
        if ch == ":" and self._match(":"):
            self._add(TT.SCOPE, "::", line=line, col=col); return
        if ch == ":":
            self._add(TT.COLON, ":", line=line, col=col); return

        raise LexerError(f"Unexpected character {ch!r}", line, col)

    def _scan_identifier(self, line, col):
        start = self.pos
        while self.pos < len(self.src) and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        lex = self.src[start:self.pos]
        if lex in TYPE_KEYWORDS:
            self._add(TT.TYPE, lex, lex, line=line, col=col)
        elif lex == "true":
            self._add(TT.BOOL_LIT, lex, True, line=line, col=col)
        elif lex == "false":
            self._add(TT.BOOL_LIT, lex, False, line=line, col=col)
        elif lex in KEYWORDS:
            self._add(TT.KEYWORD, lex, lex, line=line, col=col)
        else:
            self._add(TT.IDENT, lex, lex, line=line, col=col)

    def _scan_number(self, line, col):
        start = self.pos
        is_float = False
        while self.pos < len(self.src) and self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            self._advance()
            while self.pos < len(self.src) and self._peek().isdigit():
                self._advance()
        if self._peek() in ("f", "F"):
            is_float = True
            self._advance()
        lex = self.src[start:self.pos]
        if is_float:
            self._add(TT.FLOAT_LIT, lex, float(lex.rstrip("fF")), line=line, col=col)
        else:
            self._add(TT.INT_LIT, lex, int(lex), line=line, col=col)

    def _scan_string(self, line, col):
        self._advance()  # opening "
        chars = []
        while self.pos < len(self.src) and self._peek() != '"':
            ch = self._advance()
            if ch == "\\" and self.pos < len(self.src):
                esc = self._advance()
                chars.append({"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "0": "\0"}.get(esc, esc))
            else:
                chars.append(ch)
        if self.pos >= len(self.src):
            raise LexerError("Unterminated string literal", line, col)
        self._advance()  # closing "
        s = "".join(chars)
        self._add(TT.STRING_LIT, f'"{s}"', s, line=line, col=col)

    def _scan_char(self, line, col):
        self._advance()
        if self._peek() == "\\":
            self._advance()
            esc = self._advance()
            value = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", "0": "\0"}.get(esc, esc)
        else:
            value = self._advance()
        if self._peek() != "'":
            raise LexerError("Unterminated char literal", line, col)
        self._advance()
        self._add(TT.CHAR_LIT, f"'{value}'", value, line=line, col=col)
