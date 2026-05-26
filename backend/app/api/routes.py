"""Compile / run REST endpoints."""
from fastapi import APIRouter, HTTPException
from ..compiler import Compiler
from ..models.schemas import CompileRequest, CompileResponse, RunRequest, RunResponse

router = APIRouter(prefix="", tags=["compiler"])
_compiler = Compiler()


@router.post("/compile", response_model=CompileResponse)
def compile_endpoint(req: CompileRequest):
    if not req.source_code.strip():
        raise HTTPException(status_code=400, detail="source_code is required")
    r = _compiler.compile(req.source_code)
    return CompileResponse(
        success=r.success, tokens=r.tokens, ast=r.ast,
        symbol_table=r.symbol_table, bytecode_text=r.bytecode_text,
        bytecode=r.bytecode, errors=r.errors,
    )


@router.post("/run", response_model=RunResponse)
def run_endpoint(req: RunRequest):
    if not req.source_code.strip():
        raise HTTPException(status_code=400, detail="source_code is required")
    out = _compiler.run(req.source_code, stdin=req.stdin)
    return RunResponse(**out)


@router.get("/health")
def health():
    return {"status": "ok"}
