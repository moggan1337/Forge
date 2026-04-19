"""
Type system definitions and mappings for Forge.

This module defines the type systems for each supported language and
provides intelligent mapping between them.
"""

from __future__ import annotations

from forge.types.type_mapper import TypeMapper, TypeMapping, TypeSystem
from forge.types.primitive_types import (
    PrimitiveType,
    get_primitive_mapping,
    get_type_converter,
)

__all__ = [
    "TypeMapper",
    "TypeMapping",
    "TypeSystem",
    "PrimitiveType",
    "get_primitive_mapping",
    "get_type_converter",
]
