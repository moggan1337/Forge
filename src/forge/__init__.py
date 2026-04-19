"""
Forge - AI-Assisted Language Transpiler

A comprehensive tool for converting source code between programming languages
while preserving semantics, idioms, and best practices of the target language.

Example usage:
    >>> from forge import Transpiler
    >>> transpiler = Transpiler(source_lang="typescript", target_lang="python")
    >>> result = transpiler.transpile("const x: number = 42;")
    >>> print(result.code)
    x: int = 42
"""

__version__ = "0.1.0"
__author__ = "Forge Team"
__license__ = "MIT"

from forge.transpiler.core import Transpiler, TranspilerConfig, TranspileResult
from forge.transpiler.language import Language, LanguagePair
from forge.types.type_mapper import TypeMapper, TypeMapping

__all__ = [
    # Main transpiler
    "Transpiler",
    "TranspilerConfig",
    "TranspileResult",
    # Languages
    "Language",
    "LanguagePair",
    # Type system
    "TypeMapper",
    "TypeMapping",
    # Version info
    "__version__",
    "__author__",
    "__license__",
]
