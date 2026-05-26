"""Stack-based bytecode (Intermediate Representation) generator + VM.

Instructions:
    LOAD_CONST val      push literal
    LOAD name           push variable
    STORE name          pop -> variable
    BINOP op            pop b, a, push (a op b)
    UNOP op             pop a, push (op a)
    JUMP target         unconditional
    JUMP_IF_FALSE t     pop, jump if falsy
    CALL name argc      call function
    RETURN              return top of stack (or void)
    PRINT n             pop n values and print joined
    INPUT name          read from input queue into variable
    POP                 discard top
    LABEL name          marker (resolved to index)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from ..ast.nodes import (
    Program, FuncDecl, VarDecl, Block, If, While, For, Return, Break, Continue,
    ExprStmt, BinaryOp, UnaryOp, Assign, Call, Identifier, IntLit, FloatLit,
    BoolLit, CharLit, StringLit, CoutStmt, CinStmt, Node,
)


@dataclass
class Instr:
    op: str
    args: tuple = ()
    def __repr__(self):
        return f"{self.op:<14} {' '.join(map(repr, self.args))}".rstrip()


@dataclass
class Function:
    name: str
    params: List[str]
    code: List[Instr] = field(default_factory=list)


class CodeGenerator:
    """Emits bytecode functions per FuncDecl."""

    def __init__(self):
        self.functions: Dict[str, Function] = {}
        self.current: Optional[Function] = None
        self._label_counter = 0
        self._loop_stack: List[tuple] = []  # (continue_label, break_label)

    def generate(self, program: Program) -> Dict[str, Function]:
        for d in program.declarations:
            if isinstance(d, FuncDecl):
                self._gen_function(d)
        return self.functions

    # ── helpers ───────────────────────────────────────────
    def _emit(self, op: str, *args):
        self.current.code.append(Instr(op, args))

    def _label(self, hint="L") -> str:
        self._label_counter += 1
        return f"{hint}_{self._label_counter}"

    def _resolve_labels(self, fn: Function):
        positions = {}
        cleaned = []
        for ins in fn.code:
            if ins.op == "LABEL":
                positions[ins.args[0]] = len(cleaned)
            else:
                cleaned.append(ins)
        for i, ins in enumerate(cleaned):
            if ins.op in ("JUMP", "JUMP_IF_FALSE"):
                cleaned[i] = Instr(ins.op, (positions[ins.args[0]],))
        fn.code = cleaned

    # ── functions ─────────────────────────────────────────
    def _gen_function(self, fn: FuncDecl):
        self.current = Function(fn.name, [p.name for p in fn.params])
        # parameters are bound by the VM; emit nothing
        if fn.body:
            for s in fn.body.statements:
                self._gen(s)
        # ensure function ends with RETURN
        if not self.current.code or self.current.code[-1].op != "RETURN":
            self._emit("RETURN")
        self._resolve_labels(self.current)
        self.functions[fn.name] = self.current
        self.current = None

    # ── dispatch ──────────────────────────────────────────
    def _gen(self, n: Node):
        getattr(self, f"_g_{type(n).__name__}", self._g_noop)(n)

    def _g_noop(self, n): pass

    # statements
    def _g_VarDecl(self, n: VarDecl):
        if n.init is not None:
            self._gen(n.init)
        else:
            default = {"int": 0, "long": 0, "short": 0, "char": 0,
                       "float": 0.0, "double": 0.0, "bool": False, "string": ""}.get(n.var_type, 0)
            self._emit("LOAD_CONST", default)
        self._emit("STORE", n.name)

    def _g_Block(self, n: Block):
        for s in n.statements: self._gen(s)

    def _g_ExprStmt(self, n: ExprStmt):
        if n.expr is None: return
        self._gen(n.expr)
        self._emit("POP")

    def _g_If(self, n: If):
        else_label = self._label("ELSE")
        end_label = self._label("ENDIF")
        self._gen(n.cond)
        self._emit("JUMP_IF_FALSE", else_label)
        self._gen(n.then_branch)
        self._emit("JUMP", end_label)
        self._emit("LABEL", else_label)
        if n.else_branch is not None:
            self._gen(n.else_branch)
        self._emit("LABEL", end_label)

    def _g_While(self, n: While):
        start = self._label("WHILE")
        end = self._label("ENDWHILE")
        self._emit("LABEL", start)
        self._gen(n.cond)
        self._emit("JUMP_IF_FALSE", end)
        self._loop_stack.append((start, end))
        self._gen(n.body)
        self._loop_stack.pop()
        self._emit("JUMP", start)
        self._emit("LABEL", end)

    def _g_For(self, n: For):
        if n.init: self._gen(n.init)
        start = self._label("FOR")
        cont = self._label("FORC")
        end = self._label("ENDFOR")
        self._emit("LABEL", start)
        if n.cond:
            self._gen(n.cond)
            self._emit("JUMP_IF_FALSE", end)
        self._loop_stack.append((cont, end))
        self._gen(n.body)
        self._loop_stack.pop()
        self._emit("LABEL", cont)
        if n.update:
            self._gen(n.update)
            self._emit("POP")
        self._emit("JUMP", start)
        self._emit("LABEL", end)

    def _g_Return(self, n: Return):
        if n.value is not None:
            self._gen(n.value)
        else:
            self._emit("LOAD_CONST", None)
        self._emit("RETURN")

    def _g_Break(self, n: Break):
        if self._loop_stack:
            self._emit("JUMP", self._loop_stack[-1][1])

    def _g_Continue(self, n: Continue):
        if self._loop_stack:
            self._emit("JUMP", self._loop_stack[-1][0])

    def _g_CoutStmt(self, n: CoutStmt):
        for p in n.parts:
            self._gen(p)
        self._emit("PRINT", len(n.parts))

    def _g_CinStmt(self, n: CinStmt):
        for name in n.targets:
            self._emit("INPUT", name)

    # expressions
    def _g_IntLit(self, n):    self._emit("LOAD_CONST", n.value)
    def _g_FloatLit(self, n):  self._emit("LOAD_CONST", n.value)
    def _g_BoolLit(self, n):   self._emit("LOAD_CONST", n.value)
    def _g_CharLit(self, n):   self._emit("LOAD_CONST", n.value)
    def _g_StringLit(self, n): self._emit("LOAD_CONST", n.value)
    def _g_Identifier(self, n: Identifier): self._emit("LOAD", n.name)

    def _g_BinaryOp(self, n: BinaryOp):
        self._gen(n.left); self._gen(n.right); self._emit("BINOP", n.op)

    def _g_UnaryOp(self, n: UnaryOp):
        if n.op in ("++", "--", "post++", "post--") and isinstance(n.operand, Identifier):
            name = n.operand.name
            delta = 1 if "++" in n.op else -1
            if n.op.startswith("post"):
                self._emit("LOAD", name)
                self._emit("LOAD", name)
                self._emit("LOAD_CONST", delta)
                self._emit("BINOP", "+")
                self._emit("STORE", name)
            else:
                self._emit("LOAD", name)
                self._emit("LOAD_CONST", delta)
                self._emit("BINOP", "+")
                self._emit("STORE", name)
                self._emit("LOAD", name)
            return
        self._gen(n.operand)
        self._emit("UNOP", n.op)

    def _g_Assign(self, n: Assign):
        if n.op == "=":
            self._gen(n.value)
        else:
            self._emit("LOAD", n.target)
            self._gen(n.value)
            self._emit("BINOP", n.op[0])
        self._emit("STORE", n.target)
        self._emit("LOAD", n.target)

    def _g_Call(self, n: Call):
        for a in n.args: self._gen(a)
        self._emit("CALL", n.callee, len(n.args))


def format_bytecode(funcs: Dict[str, Function]) -> str:
    out = []
    for name, fn in funcs.items():
        out.append(f"func {name}({', '.join(fn.params)}):")
        for i, ins in enumerate(fn.code):
            out.append(f"  {i:>3}  {ins}")
        out.append("")
    return "\n".join(out)


def bytecode_to_dict(funcs: Dict[str, Function]) -> list:
    return [
        {"name": fn.name, "params": fn.params,
         "code": [{"op": i.op, "args": list(i.args)} for i in fn.code]}
        for fn in funcs.values()
    ]
