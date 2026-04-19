"""
Unit tests for language definitions.
"""

import pytest

from forge.transpiler.language import (
    Language,
    LanguagePair,
    get_language_pair,
    get_supported_pairs,
    is_supported,
    LANGUAGE_PAIRS,
)


class TestLanguage:
    """Tests for Language enum."""

    def test_all_languages_have_extensions(self):
        """Test all languages have file extensions defined."""
        for lang in Language:
            assert len(lang.file_extensions) > 0
            assert lang.default_extension.startswith(".")

    def test_language_from_extension_typescript(self):
        """Test detecting TypeScript from extension."""
        assert Language.from_extension(".ts") == Language.TYPESCRIPT
        assert Language.from_extension(".tsx") == Language.TYPESCRIPT

    def test_language_from_extension_python(self):
        """Test detecting Python from extension."""
        assert Language.from_extension(".py") == Language.PYTHON

    def test_language_from_extension_rust(self):
        """Test detecting Rust from extension."""
        assert Language.from_extension(".rs") == Language.RUST

    def test_language_from_extension_go(self):
        """Test detecting Go from extension."""
        assert Language.from_extension(".go") == Language.GO

    def test_language_from_extension_unknown(self):
        """Test unknown extension returns None."""
        assert Language.from_extension(".xyz") is None

    def test_language_from_string(self):
        """Test getting language from string."""
        assert Language.from_string("typescript") == Language.TYPESCRIPT
        assert Language.from_string("TypeScript") == Language.TYPESCRIPT
        assert Language.from_string("python") == Language.PYTHON
        assert Language.from_string("PYTHON") == Language.PYTHON
        assert Language.from_string("rust") == Language.RUST
        assert Language.from_string("go") == Language.GO

    def test_language_from_string_unknown(self):
        """Test unknown string returns None."""
        assert Language.from_string("unknown") is None

    def test_is_typed(self):
        """Test typed language detection."""
        assert Language.TYPESCRIPT.is_typed is True
        assert Language.RUST.is_typed is True
        assert Language.GO.is_typed is True
        assert Language.PYTHON.is_typed is False
        assert Language.JAVASCRIPT.is_typed is False

    def test_is_duck_typed(self):
        """Test duck typed language detection."""
        assert Language.PYTHON.is_duck_typed is True
        assert Language.TYPESCRIPT.is_duck_typed is False

    def test_has_ownership(self):
        """Test ownership language detection."""
        assert Language.RUST.has_ownership is True
        assert Language.PYTHON.has_ownership is False

    def test_display_name(self):
        """Test display name generation."""
        assert Language.TYPESCRIPT.display_name == "TypeScript"
        assert Language.PYTHON.display_name == "Python"
        assert Language.RUST.display_name == "Rust"
        assert Language.GO.display_name == "Go"


class TestLanguagePair:
    """Tests for LanguagePair dataclass."""

    def test_create_valid_pair(self):
        """Test creating a valid language pair."""
        pair = LanguagePair(Language.TYPESCRIPT, Language.PYTHON)
        assert pair.source == Language.TYPESCRIPT
        assert pair.target == Language.PYTHON
        assert pair.difficulty == 3  # Default

    def test_same_language_raises(self):
        """Test same source and target raises error."""
        with pytest.raises(ValueError):
            LanguagePair(Language.PYTHON, Language.PYTHON)

    def test_invalid_difficulty_raises(self):
        """Test invalid difficulty raises error."""
        with pytest.raises(ValueError):
            LanguagePair(Language.TYPESCRIPT, Language.PYTHON, difficulty=0)

        with pytest.raises(ValueError):
            LanguagePair(Language.TYPESCRIPT, Language.PYTHON, difficulty=6)

    def test_key(self):
        """Test key generation."""
        pair = LanguagePair(Language.TYPESCRIPT, Language.PYTHON)
        assert pair.key == "typescript->python"

    def test_display_name(self):
        """Test display name generation."""
        pair = LanguagePair(Language.TYPESCRIPT, Language.PYTHON)
        assert pair.display_name == "TypeScript → Python"

    def test_str_representation(self):
        """Test string representation."""
        pair = LanguagePair(Language.TYPESCRIPT, Language.PYTHON)
        assert str(pair) == "typescript->python"


class TestLanguagePairFunctions:
    """Tests for language pair utility functions."""

    def test_get_language_pair_defined(self):
        """Test getting a defined language pair."""
        pair = get_language_pair(Language.TYPESCRIPT, Language.PYTHON)
        assert pair.source == Language.TYPESCRIPT
        assert pair.target == Language.PYTHON
        assert pair.difficulty == 3
        assert "Type annotations" in pair.notes

    def test_get_language_pair_undefined(self):
        """Test getting an undefined language pair returns default."""
        # This should return a default pair (though this combo might be defined)
        pair = get_language_pair(Language.TYPESCRIPT, Language.PYTHON)
        assert isinstance(pair, LanguagePair)

    def test_get_supported_pairs(self):
        """Test getting all supported pairs."""
        pairs = get_supported_pairs()
        assert len(pairs) > 0
        for pair in pairs:
            assert isinstance(pair, LanguagePair)
            assert pair.source != pair.target

    def test_is_supported_defined(self):
        """Test checking if defined pair is supported."""
        assert is_supported(Language.TYPESCRIPT, Language.PYTHON) is True

    def test_is_supported_undefined(self):
        """Test checking if undefined pair is supported."""
        # Same language should return False
        assert is_supported(Language.PYTHON, Language.PYTHON) is False


class TestLanguagePairDefinitions:
    """Tests for predefined language pairs."""

    def test_all_pairs_in_dictionary(self):
        """Test all predefined pairs are in the dictionary."""
        for pair in get_supported_pairs():
            assert pair.key in LANGUAGE_PAIRS

    def test_difficulty_range(self):
        """Test all difficulties are in valid range."""
        for pair in get_supported_pairs():
            assert 1 <= pair.difficulty <= 5

    def test_source_not_target(self):
        """Test source is not target for all pairs."""
        for pair in get_supported_pairs():
            assert pair.source != pair.target

    def test_typescript_conversions(self):
        """Test TypeScript conversion pairs exist."""
        assert "typescript->python" in LANGUAGE_PAIRS
        assert "typescript->rust" in LANGUAGE_PAIRS
        assert "typescript->go" in LANGUAGE_PAIRS

    def test_python_conversions(self):
        """Test Python conversion pairs exist."""
        assert "python->typescript" in LANGUAGE_PAIRS
        assert "python->rust" in LANGUAGE_PAIRS
        assert "python->go" in LANGUAGE_PAIRS

    def test_rust_conversions(self):
        """Test Rust conversion pairs exist."""
        assert "rust->typescript" in LANGUAGE_PAIRS
        assert "rust->python" in LANGUAGE_PAIRS
        assert "rust->go" in LANGUAGE_PAIRS

    def test_go_conversions(self):
        """Test Go conversion pairs exist."""
        assert "go->typescript" in LANGUAGE_PAIRS
        assert "go->python" in LANGUAGE_PAIRS
        assert "go->rust" in LANGUAGE_PAIRS
