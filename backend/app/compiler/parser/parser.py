"""Recursive-descent parser for a C++ subset producing an AST.

Grammar (subset):
    program        := (func_decl | var_decl ';')*
    func_decl      := type IDENT '(' params? ')' block
    params         := param (',' param)*
    param          := type IDENT
    var_decl       := type IDENT ('=' expression)?
    block          := '{' statement* '}'
    statement      := var_decl ';' | if_stmt | while_stmt | for_stmt
                    | return_stmt | break_stmt | continue_stmt | block
                    | cout_stmt ';' | cin_stmt ';' | expr_stmt
    if_stmt        := 'if' '(' expression ')' statement ('else' statement)?
    while_stmt     := 'while' '(' expression ')' statement
    for_stmt       := 'for' '(' (var_decl|expr_stmt|;) ';' expression? ';' expression? ')' statement
    return_stmt    := 'return' expression? ';'
    cout_stmt      := ('std' '::')? 'cout' ('<<' expression)+
    cin_stmt       := ('std' '::')? 'cin'  ('>>' IDENT)+
    expression     := assignment
    assignment     := logical_or (('='|'+='|'-='|'*='|'/=') assignment)?
    logical_or     := logical_and ('||' logical_and)*
    logical_and    := equality ('&&' equality)*
    equality       := relational (('=='|'!=') relational)*
    relational     := additive (('<'|'>'|'<='|'>=') additive)*
    additive       := multiplicative (('+'|'-') multiplicative)*
    multiplicative := unary (('*'|'/'|'%') unary)*
    unary          := ('!'|'-'|'+'|'++'|'--') unary | postfix
    postfix        := primary ('++'|'--')?
    primary        := literal | IDENT | call | '(' expression ')'
    call           := IDENT '(' arg_list? ')'
"""
from __future__ import annotations
from typing import List, Optional
from ..lexer import Token, TT, Lexer
from ..ast.nodes import (
    Program, FuncDecl, Param, VarDecl, Block, If, While, For, Return, Break,
    Continue, ExprStmt, BinaryOp, UnaryOp, Assign, Call, Identifier, IntLit,
    FloatLit, BoolLit, CharLit, StringLit, CoutStmt, CinStmt,
)


class ParseError(Exception):
    def __init__(self, msg: str, token: Token):
        super().__init__(f"[Parse error] line {token.line}:{token.col}: {msg} (at {token.lexeme!r})")
        self.token = token


class Parser:
    """Builds an AST from a token stream."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── helpers ────────────────────────────────────────────
    def _peek(self, off: int = 0) -> Token:
        p = min(self.pos + off, len(self.tokens) - 1)
        return self.tokens[p]

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        if t.type != TT.EOF:
            self.pos += 1
        return t

    def _check(self, *types: TT) -> bool:
        return self._peek().type in types

    def _check_kw(self, *names: str) -> bool:
        t = self._peek()
        return t.type == TT.KEYWORD and t.lexeme in names

    def _match(self, *types: TT) -> Optional[Token]:
        if self._check(*types):
            return self._advance()
        return None

    def _match_kw(self, *names: str) -> Optional[Token]:
        if self._check_kw(*names):
            return self._advance()
        return None

    def _expect(self, ttype: TT, msg: str) -> Token:
        if self._check(ttype):
            return self._advance()
        raise ParseError(msg, self._peek())

    # ── entry ──────────────────────────────────────────────
    def parse(self) -> Program:
        prog = Program(line=1, declarations=[])
        while not self._check(TT.EOF):
            # Skip stray 'using namespace std;'
            if self._check_kw("using"):
                while not self._check(TT.SEMI) and not self._check(TT.EOF):
                    self._advance()
                self._match(TT.SEMI)
                continue
            decl = self._top_level()
            if decl is not None:
                prog.declarations.append(decl)
        return prog

    def _top_level(self):
        # type IDENT '(' -> function ; otherwise var decl
        if self._check(TT.TYPE):
            t = self.pos
            self._advance()  # type
            if self._check(TT.IDENT) and self._peek(1).type == TT.LPAREN:
                self.pos = t
                return self._func_decl()
            self.pos = t
            decl = self._var_decl()
            self._expect(TT.SEMI, "Expected ';' after declaration")
            return decl
        raise ParseError("Expected declaration", self._peek())

    def _func_decl(self) -> FuncDecl:
        rtype = self._advance().lexeme
        name = self._expect(TT.IDENT, "Expected function name").lexeme
        self._expect(TT.LPAREN, "Expected '('")
        params: List[Param] = []
        if not self._check(TT.RPAREN):
            params.append(self._param())
            while self._match(TT.COMMA):
                params.append(self._param())
        self._expect(TT.RPAREN, "Expected ')'")
        body = self._block()
        return FuncDecl(line=body.line, return_type=rtype, name=name, params=params, body=body)

    def _param(self) -> Param:
        t = self._expect(TT.TYPE, "Expected parameter type")
        name = self._expect(TT.IDENT, "Expected parameter name").lexeme
        return Param(line=t.line, param_type=t.lexeme, name=name)

    def _var_decl(self) -> VarDecl:
        t = self._expect(TT.TYPE, "Expected type")
        name = self._expect(TT.IDENT, "Expected identifier").lexeme
        init = None
        if self._match(TT.ASSIGN):
            init = self._expression()
        return VarDecl(line=t.line, var_type=t.lexeme, name=name, init=init)

    # ── statements ────────────────────────────────────────
    def _block(self) -> Block:
        tok = self._expect(TT.LBRACE, "Expected '{'")
        stmts = []
        while not self._check(TT.RBRACE) and not self._check(TT.EOF):
            stmts.append(self._statement())
        self._expect(TT.RBRACE, "Expected '}'")
        return Block(line=tok.line, statements=stmts)

    def _statement(self):
        if self._check(TT.LBRACE):
            return self._block()
        if self._check_kw("if"):    return self._if_stmt()
        if self._check_kw("while"): return self._while_stmt()
        if self._check_kw("for"):   return self._for_stmt()
        if self._check_kw("return"):
            t = self._advance()
            value = None
            if not self._check(TT.SEMI):
                value = self._expression()
            self._expect(TT.SEMI, "Expected ';'")
            return Return(line=t.line, value=value)
        if self._check_kw("break"):
            t = self._advance(); self._expect(TT.SEMI, "Expected ';'")
            return Break(line=t.line)
        if self._check_kw("continue"):
            t = self._advance(); self._expect(TT.SEMI, "Expected ';'")
            return Continue(line=t.line)
        if self._check(TT.TYPE):
            d = self._var_decl()
            self._expect(TT.SEMI, "Expected ';'")
            return d
        if self._check_kw("cout") or (self._check_kw("std") and self._peek(1).type == TT.SCOPE and self._peek(2).lexeme == "cout"):
            return self._cout_stmt()
        if self._check_kw("cin") or (self._check_kw("std") and self._peek(1).type == TT.SCOPE and self._peek(2).lexeme == "cin"):
            return self._cin_stmt()
        # expression statement
        expr = self._expression()
        tok = self._expect(TT.SEMI, "Expected ';'")
        return ExprStmt(line=tok.line, expr=expr)

    def _if_stmt(self):
        t = self._advance()
        self._expect(TT.LPAREN, "Expected '(' after 'if'")
        cond = self._expression()
        self._expect(TT.RPAREN, "Expected ')'")
        then_b = self._statement()
        else_b = None
        if self._match_kw("else"):
            else_b = self._statement()
        return If(line=t.line, cond=cond, then_branch=then_b, else_branch=else_b)

    def _while_stmt(self):
        t = self._advance()
        self._expect(TT.LPAREN, "Expected '('")
        cond = self._expression()
        self._expect(TT.RPAREN, "Expected ')'")
        body = self._statement()
        return While(line=t.line, cond=cond, body=body)

    def _for_stmt(self):
        t = self._advance()
        self._expect(TT.LPAREN, "Expected '('")
        init = None
        if not self._check(TT.SEMI):
            if self._check(TT.TYPE):
                init = self._var_decl()
            else:
                init = ExprStmt(line=t.line, expr=self._expression())
        self._expect(TT.SEMI, "Expected ';'")
        cond = None
        if not self._check(TT.SEMI):
            cond = self._expression()
        self._expect(TT.SEMI, "Expected ';'")
        update = None
        if not self._check(TT.RPAREN):
            update = self._expression()
        self._expect(TT.RPAREN, "Expected ')'")
        body = self._statement()
        return For(line=t.line, init=init, cond=cond, update=update, body=body)

    def _cout_stmt(self):
        # optional std::
        if self._check_kw("std"):
            self._advance(); self._expect(TT.SCOPE, "Expected '::'")
        t = self._advance()  # 'cout'
        parts = []
        while self._match(TT.SHL):
            # endl handled as identifier sentinel
            if self._check_kw("endl"):
                end_tok = self._advance()
                parts.append(StringLit(line=end_tok.line, value="\n"))
            elif self._check_kw("std") and self._peek(1).type == TT.SCOPE and self._peek(2).lexeme == "endl":
                self._advance(); self._advance()
                end_tok = self._advance()
                parts.append(StringLit(line=end_tok.line, value="\n"))
            else:
                parts.append(self._expression())
        self._expect(TT.SEMI, "Expected ';'")
        return CoutStmt(line=t.line, parts=parts)

    def _cin_stmt(self):
        if self._check_kw("std"):
            self._advance(); self._expect(TT.SCOPE, "Expected '::'")
        t = self._advance()
        targets = []
        while self._match(TT.SHR):
            ident = self._expect(TT.IDENT, "Expected identifier after '>>'").lexeme
            targets.append(ident)
        self._expect(TT.SEMI, "Expected ';'")
        return CinStmt(line=t.line, targets=targets)

    # ── expressions ───────────────────────────────────────
    def _expression(self):
        return self._assignment()

    def _assignment(self):
        left = self._logical_or()
        if self._check(TT.ASSIGN, TT.PLUS_ASSIGN, TT.MINUS_ASSIGN, TT.STAR_ASSIGN, TT.SLASH_ASSIGN):
            op_tok = self._advance()
            value = self._assignment()
            if not isinstance(left, Identifier):
                raise ParseError("Invalid assignment target", op_tok)
            return Assign(line=op_tok.line, target=left.name, op=op_tok.lexeme, value=value)
        return left

    def _binary(self, sub, *ops):
        left = sub()
        while self._check(*ops):
            op = self._advance()
            right = sub()
            left = BinaryOp(line=op.line, op=op.lexeme, left=left, right=right)
        return left

    def _logical_or(self):    return self._binary(self._logical_and, TT.OR)
    def _logical_and(self):   return self._binary(self._equality, TT.AND)
    def _equality(self):      return self._binary(self._relational, TT.EQ, TT.NEQ)
    def _relational(self):    return self._binary(self._additive, TT.LT, TT.GT, TT.LTE, TT.GTE)
    def _additive(self):      return self._binary(self._multiplicative, TT.PLUS, TT.MINUS)
    def _multiplicative(self):return self._binary(self._unary, TT.STAR, TT.SLASH, TT.PERCENT)

    def _unary(self):
        if self._check(TT.NOT, TT.MINUS, TT.PLUS, TT.INC, TT.DEC):
            op = self._advance()
            operand = self._unary()
            return UnaryOp(line=op.line, op=op.lexeme, operand=operand)
        return self._postfix()

    def _postfix(self):
        node = self._primary()
        if self._check(TT.INC, TT.DEC):
            op = self._advance()
            node = UnaryOp(line=op.line, op="post" + op.lexeme, operand=node)
        return node

    def _primary(self):
        t = self._peek()
        if t.type == TT.INT_LIT:    self._advance(); return IntLit(line=t.line, value=t.value)
        if t.type == TT.FLOAT_LIT:  self._advance(); return FloatLit(line=t.line, value=t.value)
        if t.type == TT.BOOL_LIT:   self._advance(); return BoolLit(line=t.line, value=t.value)
        if t.type == TT.CHAR_LIT:   self._advance(); return CharLit(line=t.line, value=t.value)
        if t.type == TT.STRING_LIT: self._advance(); return StringLit(line=t.line, value=t.value)
        if t.type == TT.LPAREN:
            self._advance()
            e = self._expression()
            self._expect(TT.RPAREN, "Expected ')'")
            return e
        if t.type == TT.IDENT:
            self._advance()
            if self._match(TT.LPAREN):
                args = []
                if not self._check(TT.RPAREN):
                    args.append(self._expression())
                    while self._match(TT.COMMA):
                        args.append(self._expression())
                self._expect(TT.RPAREN, "Expected ')'")
                return Call(line=t.line, callee=t.lexeme, args=args)
            return Identifier(line=t.line, name=t.lexeme)
        raise ParseError("Unexpected token in expression", t)
