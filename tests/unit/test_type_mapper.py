"""
Unit tests for the type mapper.
"""

import pytest

from forge.transpiler.language import Language
from forge.types.type_mapper import TypeMapper, TypeMapping


class TestTypeMapper:
    """Tests for TypeMapper class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = TypeMapper()

    # Primitive type mappings
    def test_map_number_to_python(self):
        """Test mapping TypeScript number to Python."""
        result = self.mapper.map_type("number", Language.TYPESCRIPT, Language.PYTHON)
        assert result.target_type == "float | int"
        assert result.quality == "exact"

    def test_map_number_to_rust(self):
        """Test mapping TypeScript number to Rust."""
        result = self.mapper.map_type("number", Language.TYPESCRIPT, Language.RUST)
        assert result.target_type == "f64"
        assert result.quality == "exact"

    def test_map_number_to_go(self):
        """Test mapping TypeScript number to Go."""
        result = self.mapper.map_type("number", Language.TYPESCRIPT, Language.GO)
        assert result.target_type == "float64"
        assert result.quality == "exact"

    def test_map_string_to_python(self):
        """Test mapping TypeScript string to Python."""
        result = self.mapper.map_type("string", Language.TYPESCRIPT, Language.PYTHON)
        assert result.target_type == "str"
        assert result.quality == "exact"

    def test_map_string_to_rust(self):
        """Test mapping TypeScript string to Rust."""
        result = self.mapper.map_type("string", Language.TYPESCRIPT, Language.RUST)
        assert result.target_type == "String"
        assert result.quality == "exact"

    def test_map_boolean_to_python(self):
        """Test mapping TypeScript boolean to Python."""
        result = self.mapper.map_type("boolean", Language.TYPESCRIPT, Language.PYTHON)
        assert result.target_type == "bool"
        assert result.quality == "exact"

    def test_map_null_to_python(self):
        """Test mapping TypeScript null to Python."""
        result = self.mapper.map_type("null", Language.TYPESCRIPT, Language.PYTHON)
        assert result.target_type == "None"
        assert result.quality == "exact"

    def test_map_any_to_python(self):
        """Test mapping TypeScript any to Python."""
        result = self.mapper.map_type("any", Language.TYPESCRIPT, Language.PYTHON)
        assert result.target_type == "Any"
        assert result.quality == "exact"
        assert result.requires_import is True

    # Python to TypeScript
    def test_map_python_str_to_typescript(self):
        """Test mapping Python str to TypeScript."""
        result = self.mapper.map_type("str", Language.PYTHON, Language.TYPESCRIPT)
        assert result.target_type == "string"
        assert result.quality == "exact"

    def test_map_python_int_to_typescript(self):
        """Test mapping Python int to TypeScript."""
        result = self.mapper.map_type("int", Language.PYTHON, Language.TYPESCRIPT)
        assert result.target_type == "number"
        assert result.quality == "exact"

    def test_map_python_bool_to_typescript(self):
        """Test mapping Python bool to TypeScript."""
        result = self.mapper.map_type("bool", Language.PYTHON, Language.TYPESCRIPT)
        assert result.target_type == "boolean"
        assert result.quality == "exact"

    def test_map_python_list_to_typescript(self):
        """Test mapping Python list to TypeScript."""
        result = self.mapper.map_type("list", Language.PYTHON, Language.TYPESCRIPT)
        assert result.quality == "close"

    # Array types
    def test_map_array_type(self):
        """Test mapping array types."""
        result = self.mapper.map_type("string[]", Language.TYPESCRIPT, Language.PYTHON)
        assert "list" in result.target_type.lower() or "List" in result.target_type

    def test_map_array_type_to_rust(self):
        """Test mapping array types to Rust."""
        result = self.mapper.map_type("string[]", Language.TYPESCRIPT, Language.RUST)
        assert "Vec" in result.target_type or "vec" in result.target_type

    # Same language (no-op)
    def test_same_language(self):
        """Test mapping same language returns no-op."""
        result = self.mapper.map_type("string", Language.TYPESCRIPT, Language.TYPESCRIPT)
        assert result.source_type == result.target_type
        assert result.quality == "exact"

    # Unknown types
    def test_unknown_type(self):
        """Test handling of unknown types."""
        result = self.mapper.map_type("MyCustomType", Language.TYPESCRIPT, Language.PYTHON)
        assert result.target_type == "MyCustomType"
        assert result.quality == "approximate"
        assert result.needs_review is True

    # Custom mappings
    def test_add_custom_mapping(self):
        """Test adding custom type mappings."""
        self.mapper.add_custom_mapping(
            source_type="MyType",
            target_type="CustomType",
            source_lang=Language.TYPESCRIPT,
            target_lang=Language.PYTHON,
            quality="exact",
        )

        result = self.mapper.map_type("MyType", Language.TYPESCRIPT, Language.PYTHON)
        assert result.target_type == "CustomType"
        assert result.quality == "exact"

    # Import collection
    def test_get_imports_for_mapping(self):
        """Test collecting required imports."""
        mappings = [
            TypeMapping(
                source_type="any",
                target_type="Any",
                requires_import=True,
                import_statement="from typing import Any",
            ),
            TypeMapping(
                source_type="Optional",
                target_type="Optional",
                requires_import=True,
                import_statement="from typing import Optional",
            ),
        ]

        imports = self.mapper.get_imports_for_mapping(mappings)
        assert len(imports) == 2
        assert any("typing" in imp for imp in imports)


class TestTypeMapping:
    """Tests for TypeMapping dataclass."""

    def test_exact_quality(self):
        """Test exact quality type mapping."""
        mapping = TypeMapping(
            source_type="string",
            target_type="str",
            quality="exact",
        )
        assert mapping.is_exact is True
        assert mapping.needs_review is False

    def test_close_quality(self):
        """Test close quality type mapping."""
        mapping = TypeMapping(
            source_type="Array<T>",
            target_type="list[T]",
            quality="close",
        )
        assert mapping.is_exact is False
        assert mapping.needs_review is True

    def test_approximate_quality(self):
        """Test approximate quality type mapping."""
        mapping = TypeMapping(
            source_type="unknown",
            target_type="Any",
            quality="approximate",
        )
        assert mapping.is_exact is False
        assert mapping.needs_review is True

    def test_invalid_quality(self):
        """Test invalid quality raises error."""
        with pytest.raises(ValueError):
            TypeMapping(
                source_type="string",
                target_type="str",
                quality="invalid",
            )
