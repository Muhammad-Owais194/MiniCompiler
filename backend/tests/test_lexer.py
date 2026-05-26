from app.compiler.lexer import Lexer, TT

def test_basic_tokens():
    toks = Lexer("int x = 42;").tokenize()
    kinds = [t.type for t in toks]
    assert TT.TYPE in kinds and TT.IDENT in kinds and TT.INT_LIT in kinds

def test_operators():
    toks = Lexer("a <= b && c++").tokenize()
    lex = [t.lexeme for t in toks]
    assert "<=" in lex and "&&" in lex and "++" in lex

def test_string_and_char():
    toks = Lexer('"hi" \'a\'').tokenize()
    assert toks[0].type == TT.STRING_LIT and toks[1].type == TT.CHAR_LIT
