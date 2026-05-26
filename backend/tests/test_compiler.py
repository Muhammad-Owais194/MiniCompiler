from app.compiler import Compiler

SRC = """
#include <iostream>
using namespace std;

int add(int a, int b) { return a + b; }

int main() {
    int x = 10;
    int y = 32;
    int z = add(x, y);
    if (z > 40) {
        cout << "big: " << z << endl;
    } else {
        cout << "small" << endl;
    }
    for (int i = 0; i < 3; i = i + 1) {
        cout << i << endl;
    }
    return 0;
}
"""

def test_compile_ok():
    r = Compiler().compile(SRC)
    assert r.success, r.errors
    assert any(s["name"] == "main" for s in r.symbol_table)

def test_run_ok():
    out = Compiler().run(SRC)
    assert out["success"], out["errors"]
    assert "big: 42" in out["stdout"]
    assert "0\n1\n2\n" in out["stdout"]

def test_semantic_error():
    r = Compiler().compile("int main(){ y = 1; return 0; }")
    assert not r.success
    assert any("undefined" in e for e in r.errors)
