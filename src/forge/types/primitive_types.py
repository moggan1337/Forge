"""
Primitive type definitions and converters for Forge.

Provides comprehensive primitive type definitions for all supported languages
and utilities for type conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from forge.transpiler.language import Language


class PrimitiveType(Enum):
    """Enumeration of all primitive types across supported languages."""

    # Numeric types
    INT = "int"
    FLOAT = "float"
    DOUBLE = "double"
    DECIMAL = "decimal"
    BIGINT = "bigint"
    NUMBER = "number"

    # Text types
    STRING = "string"
    CHAR = "char"
    RUNE = "rune"

    # Boolean
    BOOLEAN = "boolean"
    BOOL = "bool"

    # Null/void types
    NULL = "null"
    NIL = "nil"
    NONE = "None"
    VOID = "void"
    UNDEFINED = "undefined"

    # Special types
    ANY = "any"
    UNKNOWN = "unknown"
    NEVER = "never"
    OBJECT = "object"
    DYNAMIC = "dynamic"

    # Byte types
    BYTE = "byte"
    BYTES = "bytes"


@dataclass
class PrimitiveTypeInfo:
    """Detailed information about a primitive type."""

    name: str
    primitive_type: PrimitiveType
    default_value: str
    size_bytes: Optional[int] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    language: Optional[Language] = None


# Primitive type information by language
PRIMITIVE_INFO: dict[Language, dict[str, PrimitiveTypeInfo]] = {
    Language.TYPESCRIPT: {
        "number": PrimitiveTypeInfo("number", PrimitiveType.NUMBER, "0", 8, "-9007199254740991", "9019254740991"),
        "string": PrimitiveTypeInfo("string", PrimitiveType.STRING, '""', None),
        "boolean": PrimitiveTypeInfo("boolean", PrimitiveType.BOOLEAN, "false", 1),
        "null": PrimitiveTypeInfo("null", PrimitiveType.NULL, "null", None),
        "undefined": PrimitiveTypeInfo("undefined", PrimitiveType.UNDEFINED, "undefined", None),
        "void": PrimitiveTypeInfo("void", PrimitiveType.VOID, "void", None),
        "any": PrimitiveTypeInfo("any", PrimitiveType.ANY, "undefined", None),
        "unknown": PrimitiveTypeInfo("unknown", PrimitiveType.UNKNOWN, "undefined", None),
        "never": PrimitiveTypeInfo("never", PrimitiveType.NEVER, "undefined", None),
        "object": PrimitiveTypeInfo("object", PrimitiveType.OBJECT, "{}", None),
        "bigint": PrimitiveTypeInfo("bigint", PrimitiveType.BIGINT, "0n", None),
        "symbol": PrimitiveTypeInfo("symbol", PrimitiveType.STRING, "Symbol()", None),
    },
    Language.PYTHON: {
        "int": PrimitiveTypeInfo("int", PrimitiveType.INT, "0", None, None, None),
        "float": PrimitiveTypeInfo("float", PrimitiveType.FLOAT, "0.0", None, None, None),
        "str": PrimitiveTypeInfo("str", PrimitiveType.STRING, '""', None),
        "bool": PrimitiveTypeInfo("bool", PrimitiveType.BOOLEAN, "False", 1, "0", "1"),
        "bytes": PrimitiveTypeInfo("bytes", PrimitiveType.BYTES, "b''", None),
        "bytearray": PrimitiveTypeInfo("bytearray", PrimitiveType.BYTES, "bytearray()", None),
        "None": PrimitiveTypeInfo("None", PrimitiveType.NONE, "None", None),
        "object": PrimitiveTypeInfo("object", PrimitiveType.OBJECT, "object()", None),
        "type": PrimitiveTypeInfo("type", PrimitiveType.DYNAMIC, "type", None),
    },
    Language.RUST: {
        "i8": PrimitiveTypeInfo("i8", PrimitiveType.INT, "0", 1, "-128", "127"),
        "i16": PrimitiveTypeInfo("i16", PrimitiveType.INT, "0", 2, "-32768", "32767"),
        "i32": PrimitiveTypeInfo("i32", PrimitiveType.INT, "0", 4, "-2147483648", "2147483647"),
        "i64": PrimitiveTypeInfo("i64", PrimitiveType.INT, "0", 8, "-9223372036854775808", "9223372036854775807"),
        "i128": PrimitiveTypeInfo("i128", PrimitiveType.INT, "0", 16, None, None),
        "isize": PrimitiveTypeInfo("isize", PrimitiveType.INT, "0", None, None, None),
        "u8": PrimitiveTypeInfo("u8", PrimitiveType.INT, "0", 1, "0", "255"),
        "u16": PrimitiveTypeInfo("u16", PrimitiveType.INT, "0", 2, "0", "65535"),
        "u32": PrimitiveTypeInfo("u32", PrimitiveType.INT, "0", 4, "0", "4294967295"),
        "u64": PrimitiveTypeInfo("u64", PrimitiveType.INT, "0", 8, "0", "18446744073709551615"),
        "u128": PrimitiveTypeInfo("u128", PrimitiveType.INT, "0", 16, None, None),
        "usize": PrimitiveTypeInfo("usize", PrimitiveType.INT, "0", None, None, None),
        "f32": PrimitiveTypeInfo("f32", PrimitiveType.FLOAT, "0.0", 4, None, None),
        "f64": PrimitiveTypeInfo("f64", PrimitiveType.FLOAT, "0.0", 8, None, None),
        "bool": PrimitiveTypeInfo("bool", PrimitiveType.BOOLEAN, "false", 1, "0", "1"),
        "char": PrimitiveTypeInfo("char", PrimitiveType.CHAR, "'\\0'", 4, "'\\u{0}'", "'\\u{10FFFF}'"),
        "str": PrimitiveTypeInfo("str", PrimitiveType.STRING, '""', None),
        "String": PrimitiveTypeInfo("String", PrimitiveType.STRING, 'String::new()', None),
        "()": PrimitiveTypeInfo("()", PrimitiveType.VOID, "()", None),
        "!": PrimitiveTypeInfo("!", PrimitiveType.NEVER, "panic!()", None),
    },
    Language.GO: {
        "int": PrimitiveTypeInfo("int", PrimitiveType.INT, "0", None, None, None),
        "int8": PrimitiveTypeInfo("int8", PrimitiveType.INT, "0", 1, "-128", "127"),
        "int16": PrimitiveTypeInfo("int16", PrimitiveType.INT, "0", 2, "-32768", "32767"),
        "int32": PrimitiveTypeInfo("int32", PrimitiveType.INT, "0", 4, "-2147483648", "2147483647"),
        "int64": PrimitiveTypeInfo("int64", PrimitiveType.INT, "0", 8, "-9223372036854775808", "9223372036854775807"),
        "uint": PrimitiveTypeInfo("uint", PrimitiveType.INT, "0", None, None, None),
        "uint8": PrimitiveTypeInfo("uint8", PrimitiveType.INT, "0", 1, "0", "255"),
        "uint16": PrimitiveTypeInfo("uint16", PrimitiveType.INT, "0", 2, "0", "65535"),
        "uint32": PrimitiveTypeInfo("uint32", PrimitiveType.INT, "0", 4, "0", "4294967295"),
        "uint64": PrimitiveTypeInfo("uint64", PrimitiveType.INT, "0", 8, "0", "18446744073709551615"),
        "uintptr": PrimitiveTypeInfo("uintptr", PrimitiveType.INT, "0", None, None, None),
        "float32": PrimitiveTypeInfo("float32", PrimitiveType.FLOAT, "0.0", 4, None, None),
        "float64": PrimitiveTypeInfo("float64", PrimitiveType.FLOAT, "0.0", 8, None, None),
        "complex64": PrimitiveTypeInfo("complex64", PrimitiveType.DECIMAL, "0", 8, None, None),
        "complex128": PrimitiveTypeInfo("complex128", PrimitiveType.DECIMAL, "0", 16, None, None),
        "bool": PrimitiveTypeInfo("bool", PrimitiveType.BOOLEAN, "false", 1, "0", "1"),
        "byte": PrimitiveTypeInfo("byte", PrimitiveType.BYTE, "0", 1, "0", "255"),
        "rune": PrimitiveTypeInfo("rune", PrimitiveType.CHAR, "0", 4, "0", "4294967295"),
        "string": PrimitiveTypeInfo("string", PrimitiveType.STRING, '""', None),
        "error": PrimitiveTypeInfo("error", PrimitiveType.DYNAMIC, "nil", None),
    },
}


# Type mapping tables
def get_primitive_mapping(
    source_type: str,
    source_lang: Language,
    target_lang: Language,
) -> Optional[str]:
    """
    Get the equivalent primitive type in the target language.

    Args:
        source_type: Type name in source language
        source_lang: Source language
        target_lang: Target language

    Returns:
        Equivalent type name in target language, or None if no mapping exists
    """
    # Get source type info
    source_info = PRIMITIVE_INFO.get(source_lang, {}).get(source_type)
    if not source_info:
        # Try to find by primitive type enum
        for lang_info in PRIMITIVE_INFO.values():
            for info in lang_info.values():
                if info.name == source_type:
                    source_info = info
                    break

    if not source_info:
        return None

    # Find equivalent in target language
    target_info = PRIMITIVE_INFO.get(target_lang, {})
    for target_name, info in target_info.items():
        if info.primitive_type == source_info.primitive_type:
            return target_name

    return None


def get_type_converter(
    source_lang: Language,
    target_lang: Language,
) -> Optional[Callable[[str], str]]:
    """
    Get a function to convert type expressions between languages.

    Args:
        source_lang: Source language
        target_lang: Target language

    Returns:
        Conversion function, or None if no special conversion needed
    """
    # This would return specialized converters for complex type expressions
    # For now, return None and use the general TypeMapper
    return None


def infer_type_from_value(value: str, language: Language) -> Optional[str]:
    """
    Infer the type of a literal value.

    Args:
        value: The literal value
        language: The language to infer type for

    Returns:
        Type name, or None if inference fails
    """
    # String detection
    if (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
        or (value.startswith("`") and value.endswith("`"))
    ):
        return PRIMITIVE_INFO.get(language, {}).get("string", PRIMITIVE_INFO.get(language, {}).get("str")) and (
            list(PRIMITIVE_INFO[language].keys())[2]
            if len(PRIMITIVE_INFO.get(language, {})) > 2
            else "string"
        )

    # Boolean detection
    if value.lower() in ("true", "false"):
        bool_key = "boolean" if language == Language.TYPESCRIPT else "bool"
        return bool_key if bool_key in PRIMITIVE_INFO.get(language, {}) else "bool"

    # None/null/undefined
    if value.lower() in ("null", "none", "nil", "undefined"):
        none_keys = {"null", "none", "nil", "undefined"}
        for key in PRIMITIVE_INFO.get(language, {}):
            if key.lower() in none_keys:
                return key

    # Integer detection
    try:
        int(value)
        int_key = "int" if language == Language.PYTHON else ("number" if language == Language.TYPESCRIPT else "int")
        return int_key if int_key in PRIMITIVE_INFO.get(language, {}) else list(PRIMITIVE_INFO[language].keys())[0]
    except ValueError:
        pass

    # Float detection
    try:
        float(value)
        float_key = "float"
        return float_key if float_key in PRIMITIVE_INFO.get(language, {}) else list(PRIMITIVE_INFO[language].keys())[1]
    except ValueError:
        pass

    return None
