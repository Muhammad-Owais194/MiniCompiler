"""A small stack VM that executes the bytecode produced by codegen.

This is the optional execution engine — handy for /run."""
from __future__ import annotations
from typing import Dict, List, Any
from ..codegen import Function


class VMError(Exception): pass


class VM:
    def __init__(self, functions: Dict[str, Function], stdin: str = ""):
        self.functions = functions
        self.input_queue = stdin.split() if stdin else []
        self.stdout: List[str] = []

    def run(self, entry: str = "main") -> str:
        if entry not in self.functions:
            raise VMError(f"No '{entry}' function defined.")
        self._call(entry, [])
        return "".join(self.stdout)

    # ── core ──────────────────────────────────────────────
    def _call(self, name: str, args: List[Any]) -> Any:
        if name not in self.functions:
            raise VMError(f"Undefined function '{name}'")
        fn = self.functions[name]
        if len(args) != len(fn.params):
            raise VMError(f"'{name}' expects {len(fn.params)} args, got {len(args)}")
        env: Dict[str, Any] = dict(zip(fn.params, args))
        stack: List[Any] = []
        pc = 0
        code = fn.code
        max_steps = 1_000_000
        steps = 0
        while pc < len(code):
            steps += 1
            if steps > max_steps:
                raise VMError("Execution step limit exceeded (possible infinite loop).")
            ins = code[pc]
            op = ins.op
            if op == "LOAD_CONST":
                stack.append(ins.args[0]); pc += 1
            elif op == "LOAD":
                if ins.args[0] not in env:
                    raise VMError(f"Use of undefined '{ins.args[0]}'")
                stack.append(env[ins.args[0]]); pc += 1
            elif op == "STORE":
                env[ins.args[0]] = stack.pop(); pc += 1
            elif op == "POP":
                stack.pop(); pc += 1
            elif op == "BINOP":
                b = stack.pop(); a = stack.pop()
                stack.append(self._binop(ins.args[0], a, b)); pc += 1
            elif op == "UNOP":
                a = stack.pop()
                stack.append(self._unop(ins.args[0], a)); pc += 1
            elif op == "JUMP":
                pc = ins.args[0]
            elif op == "JUMP_IF_FALSE":
                v = stack.pop()
                pc = ins.args[0] if not v else pc + 1
            elif op == "CALL":
                fname, argc = ins.args
                call_args = [stack.pop() for _ in range(argc)][::-1]
                stack.append(self._call(fname, call_args))
                pc += 1
            elif op == "RETURN":
                return stack.pop() if stack else None
            elif op == "PRINT":
                n = ins.args[0]
                vals = [stack.pop() for _ in range(n)][::-1]
                self.stdout.append("".join(self._fmt(v) for v in vals))
                pc += 1
            elif op == "INPUT":
                if not self.input_queue:
                    raise VMError("cin: no more input available")
                tok = self.input_queue.pop(0)
                env[ins.args[0]] = self._coerce(tok)
                pc += 1
            else:
                raise VMError(f"Unknown opcode {op}")
        return None

    # ── ops ───────────────────────────────────────────────
    @staticmethod
    def _binop(op: str, a, b):
        if op == "+":
            if isinstance(a, str) or isinstance(b, str): return f"{a}{b}"
            return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/":
            if isinstance(a, int) and isinstance(b, int):
                if b == 0: raise VMError("Division by zero")
                return a // b
            return a / b
        if op == "%": return a % b
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "<":  return a < b
        if op == ">":  return a > b
        if op == "<=": return a <= b
        if op == ">=": return a >= b
        if op == "&&": return bool(a) and bool(b)
        if op == "||": return bool(a) or bool(b)
        raise VMError(f"Unknown binary op {op}")

    @staticmethod
    def _unop(op: str, a):
        if op == "-": return -a
        if op == "+": return +a
        if op == "!": return not a
        raise VMError(f"Unknown unary op {op}")

    @staticmethod
    def _fmt(v):
        if v is True:  return "1"
        if v is False: return "0"
        return str(v)

    @staticmethod
    def _coerce(s: str):
        try: return int(s)
        except ValueError: pass
        try: return float(s)
        except ValueError: pass
        return s
