"""
Unit tests for parsers.
"""

import pytest

from forge.parsers.base import ParseResult, ProgramNode, IdentifierNode
from forge.parsers.typescript_parser import TypeScriptParser
from forge.parsers.python_parser import PythonParser
from forge.parsers.rust_parser import RustParser
from forge.parsers.go_parser import GoParser
from forge.transpiler.language import Language


class TestTypeScriptParser:
    """Tests for TypeScript parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TypeScriptParser()

    def test_language(self):
        """Test parser language property."""
        assert self.parser.language == Language.TYPESCRIPT

    def test_parse_empty(self):
        """Test parsing empty source."""
        result = self.parser.parse("")
        # May have warnings about fallback parser
        assert result.language == Language.TYPESCRIPT

    def test_parse_simple_function(self):
        """Test parsing a simple function."""
        source = """
function hello(name: string): string {
    return "Hello, " + name;
}
"""
        result = self.parser.parse(source)
        # Result depends on tree-sitter availability
        assert result.language == Language.TYPESCRIPT
        assert isinstance(result.source_code, str)

    def test_parse_with_comments(self):
        """Test parsing with comments."""
        source = """
// This is a comment
function test() {
    // Another comment
    return true;
}
"""
        result = self.parser.parse(source)
        assert result.language == Language.TYPESCRIPT


class TestPythonParser:
    """Tests for Python parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PythonParser()

    def test_language(self):
        """Test parser language property."""
        assert self.parser.language == Language.PYTHON

    def test_parse_empty(self):
        """Test parsing empty source."""
        result = self.parser.parse("")
        assert result.success is True
        assert result.language == Language.PYTHON

    def test_parse_simple_function(self):
        """Test parsing a simple function."""
        source = """
def hello(name: str) -> str:
    return f"Hello, {name}"
"""
        result = self.parser.parse(source)
        assert result.success is True
        assert result.ast is not None

    def test_parse_class(self):
        """Test parsing a class."""
        source = """
class User:
    def __init__(self, name: str):
        self.name = name
"""
        result = self.parser.parse(source)
        assert result.success is True

    def test_parse_with_comments(self):
        """Test parsing with comments."""
        source = """
# This is a comment
def test():
    # Another comment
    return True
"""
        result = self.parser.parse(source)
        assert result.success is True

    def test_parse_syntax_error(self):
        """Test parsing with syntax error."""
        source = """
def broken(
    return None
"""
        result = self.parser.parse(source)
        assert result.success is False
        assert len(result.errors) > 0

    def test_parse_import(self):
        """Test parsing imports."""
        source = """
import os
from typing import List, Dict
"""
        result = self.parser.parse(source)
        assert result.success is True

    def test_parse_list_literal(self):
        """Test parsing list literals."""
        source = """
numbers = [1, 2, 3, 4, 5]
"""
        result = self.parser.parse(source)
        assert result.success is True

    def test_parse_dict_literal(self):
        """Test parsing dict literals."""
        source = """
config = {"name": "test", "value": 42}
"""
        result = self.parser.parse(source)
        assert result.success is True

    def test_parse_lambda(self):
        """Test parsing lambda expressions."""
        source = """
add = lambda x, y: x + y
"""
        result = self.parser.parse(source)
        assert result.success is True

    def test_parse_match(self):
        """Test parsing match statements."""
        source = """
def http_status(code):
    match code:
        case 200:
            return "OK"
        case 404:
            return "Not Found"
        case _:
            return "Unknown"
"""
        result = self.parser.parse(source)
        assert result.success is True


class TestRustParser:
    """Tests for Rust parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()

    def test_language(self):
        """Test parser language property."""
        assert self.parser.language == Language.RUST

    def test_parse_empty(self):
        """Test parsing empty source."""
        result = self.parser.parse("")
        assert result.language == Language.RUST

    def test_parse_simple_function(self):
        """Test parsing a simple function."""
        source = """
fn hello(name: &str) -> String {
    format!("Hello, {}", name)
}
"""
        result = self.parser.parse(source)
        assert result.language == Language.RUST


class TestGoParser:
    """Tests for Go parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = GoParser()

    def test_language(self):
        """Test parser language property."""
        assert self.parser.language == Language.GO

    def test_parse_empty(self):
        """Test parsing empty source."""
        result = self.parser.parse("")
        assert result.language == Language.GO

    def test_parse_simple_function(self):
        """Test parsing a simple function."""
        source = """
package main

func hello(name string) string {
    return "Hello, " + name
}
"""
        result = self.parser.parse(source)
        assert result.language == Language.GO


class TestParseResult:
    """Tests for ParseResult dataclass."""

    def test_success_result(self):
        """Test creating a successful parse result."""
        result = ParseResult(
            success=True,
            ast=ProgramNode(body=[], language=Language.PYTHON),
            language=Language.PYTHON,
        )
        assert result.has_errors is False
        assert result.has_warnings is False

    def test_result_with_errors(self):
        """Test parse result with errors."""
        from forge.parsers.base import ParseError

        result = ParseResult(
            success=False,
            errors=[
                ParseError(message="Test error", line=1, column=0),
            ],
            language=Language.PYTHON,
        )
        assert result.has_errors is True
        assert result.has_warnings is False

    def test_result_with_warnings(self):
        """Test parse result with warnings."""
        from forge.parsers.base import ParseWarning

        result = ParseResult(
            success=True,
            warnings=[
                ParseWarning(message="Test warning", line=1, column=0),
            ],
            language=Language.PYTHON,
        )
        assert result.has_errors is False
        assert result.has_warnings is True
