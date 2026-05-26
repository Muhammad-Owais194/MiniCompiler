"""Pydantic request/response models for the REST API."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, List, Optional


class CompileRequest(BaseModel):
    source_code: str = Field(..., description="C++ source code")


class RunRequest(BaseModel):
    source_code: str
    stdin: str = ""


class CompileResponse(BaseModel):
    success: bool
    tokens: List[dict] = []
    ast: Optional[dict] = None
    symbol_table: List[dict] = []
    bytecode_text: str = ""
    bytecode: List[dict] = []
    errors: List[str] = []


class RunResponse(BaseModel):
    success: bool
    stdout: str = ""
    errors: List[str] = []
