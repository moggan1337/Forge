"""
Language definitions and language pair management for Forge.

This module defines the supported programming languages, their characteristics,
and the relationships between them for transpilation purposes.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional


class Language(enum.Enum):
    """Supported programming languages in Forge."""

    TYPESCRIPT = "typescript"
    PYTHON = "python"
    RUST = "rust"
    GO = "go"
    JAVASCRIPT = "javascript"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable name for the language."""
        names = {
            Language.TYPESCRIPT: "TypeScript",
            Language.PYTHON: "Python",
            Language.RUST: "Rust",
            Language.GO: "Go",
            Language.JAVASCRIPT: "JavaScript",
        }
        return names.get(self, self.value)

    @property
    def file_extensions(self) -> tuple[str, ...]:
        """Standard file extensions for this language."""
        extensions = {
            Language.TYPESCRIPT: (".ts", ".tsx"),
            Language.PYTHON: (".py",),
            Language.RUST: (".rs",),
            Language.GO: (".go",),
            Language.JAVASCRIPT: (".js", ".jsx"),
        }
        return extensions.get(self, (".txt",))

    @property
    def default_extension(self) -> str:
        """Default file extension for this language."""
        return self.file_extensions[0]

    @property
    def is_typed(self) -> bool:
        """Whether this language has a static type system."""
        return self in {
            Language.TYPESCRIPT,
            Language.RUST,
            Language.GO,
        }

    @property
    def is_duck_typed(self) -> bool:
        """Whether this language uses duck typing."""
        return self == Language.PYTHON

    @property
    def has_ownership(self) -> bool:
        """Whether this language has ownership/memory management."""
        return self == Language.RUST

    @property
    def has_garbage_collection(self) -> bool:
        """Whether this language uses garbage collection."""
        return self in {Language.PYTHON, Language.GO, Language.JAVASCRIPT}

    @classmethod
    def from_extension(cls, ext: str) -> Optional[Language]:
        """Get language from file extension."""
        ext = ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for lang in cls:
            if ext in lang.file_extensions:
                return lang
        return None

    @classmethod
    def from_string(cls, name: str) -> Optional[Language]:
        """Get language from string name."""
        name = name.lower().strip()
        for lang in cls:
            if lang.value == name or lang.display_name.lower() == name:
                return lang
        return None


@dataclass(frozen=True)
class LanguagePair:
    """
    Represents a source-target language pair for transpilation.

    Attributes:
        source: The source language
        target: The target language
        difficulty: Estimated transpilation difficulty (1-5)
        notes: Additional notes about this language pair
    """

    source: Language
    target: Language
    difficulty: int = 3  # 1=easy, 5=hard
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate the language pair."""
        if not 1 <= self.difficulty <= 5:
            raise ValueError("Difficulty must be between 1 and 5")
        if self.source == self.target:
            raise ValueError("Source and target languages must be different")

    @property
    def key(self) -> str:
        """Unique key for this language pair."""
        return f"{self.source.value}->{self.target.value}"

    @property
    def display_name(self) -> str:
        """Human-readable name for this language pair."""
        return f"{self.source.display_name} → {self.target.display_name}"

    def __str__(self) -> str:
        return self.key


# Predefined language pairs with difficulty ratings
LANGUAGE_PAIRS: dict[str, LanguagePair] = {
    # TypeScript conversions
    "typescript->python": LanguagePair(
        Language.TYPESCRIPT,
        Language.PYTHON,
        difficulty=3,
        notes="Type annotations map to type hints. Classes and interfaces require restructuring.",
    ),
    "typescript->rust": LanguagePair(
        Language.TYPESCRIPT,
        Language.RUST,
        difficulty=4,
        notes="Requires ownership and lifetime handling. Async patterns differ significantly.",
    ),
    "typescript->go": LanguagePair(
        Language.TYPESCRIPT,
        Language.GO,
        difficulty=3,
        notes="Similar OOP patterns. TypeScript interfaces map to Go interfaces.",
    ),
    # Python conversions
    "python->typescript": LanguagePair(
        Language.PYTHON,
        Language.TYPESCRIPT,
        difficulty=2,
        notes="Python type hints map well to TypeScript. Duck typing becomes structural typing.",
    ),
    "python->rust": LanguagePair(
        Language.PYTHON,
        Language.RUST,
        difficulty=5,
        notes="Major paradigm shift. Memory management, ownership, and borrow checker.",
    ),
    "python->go": LanguagePair(
        Language.PYTHON,
        Language.GO,
        difficulty=3,
        notes="Similar high-level constructs. Go's error handling differs from exceptions.",
    ),
    # Rust conversions
    "rust->typescript": LanguagePair(
        Language.RUST,
        Language.TYPESCRIPT,
        difficulty=4,
        notes="Remove ownership concepts. Pattern matching becomes switch statements.",
    ),
    "rust->python": LanguagePair(
        Language.RUST,
        Language.PYTHON,
        difficulty=4,
        notes="Simplify memory model. Traits become protocols/ABC. Match becomes if/elif.",
    ),
    "rust->go": LanguagePair(
        Language.RUST,
        Language.GO,
        difficulty=4,
        notes="Ownership concepts removed. Go's GC vs Rust's ownership. Error handling differs.",
    ),
    # Go conversions
    "go->typescript": LanguagePair(
        Language.GO,
        Language.TYPESCRIPT,
        difficulty=2,
        notes="Structs to interfaces/classes. Goroutines become async/await.",
    ),
    "go->python": LanguagePair(
        Language.GO,
        Language.PYTHON,
        difficulty=3,
        notes="Error handling patterns differ. Goroutines become threading/asyncio.",
    ),
    "go->rust": LanguagePair(
        Language.GO,
        Language.RUST,
        difficulty=4,
        notes="GC to ownership. Interfaces to traits. Goroutines to async/Tokio.",
    ),
}


def get_language_pair(source: Language, target: Language) -> LanguagePair:
    """
    Get the LanguagePair for source and target languages.

    Args:
        source: Source language
        target: Target language

    Returns:
        LanguagePair with difficulty and notes
    """
    key = f"{source.value}->{target.value}"
    if key in LANGUAGE_PAIRS:
        return LANGUAGE_PAIRS[key]
    # Return a default pair with medium difficulty
    return LanguagePair(
        source,
        target,
        difficulty=3,
        notes="Transpilation may require manual review for best results.",
    )


def get_supported_pairs() -> list[LanguagePair]:
    """Get all supported language pairs."""
    return list(LANGUAGE_PAIRS.values())


def is_supported(source: Language, target: Language) -> bool:
    """Check if a language pair is supported."""
    return f"{source.value}->{target.value}" in LANGUAGE_PAIRS
