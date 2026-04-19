"""
AST parsing layer for Forge.

Provides language-specific AST parsing capabilities using tree-sitter
and language-specific parsers.
"""

from __future__ import annotations

from forge.parsers.base import (
    ASTNode,
    ASTVisitor,
    ParseResult,
    SourceLocation,
    SourceRange,
)
from forge.parsers.typescript_parser import TypeScriptParser
from forge.parsers.python_parser import PythonParser
from forge.parsers.rust_parser import RustParser
from forge.parsers.go_parser import GoParser

__all__ = [
    "ASTNode",
    "ASTVisitor",
    "ParseResult",
    "SourceLocation",
    "SourceRange",
    "TypeScriptParser",
    "PythonParser",
    "RustParser",
    "GoParser",
]
