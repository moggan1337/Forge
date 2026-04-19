"""
Type mapping system for Forge transpiler.

Handles conversion between type systems of different programming languages,
including primitive types, complex types, and custom type definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Protocol, TypeVar

from forge.transpiler.language import Language

T = TypeVar("T")


class TypeSystem(Enum):
    """Type system classification for languages."""

    STRUCTURAL = "structural"  # TypeScript, Go
    NOMINAL = "nominal"  # Rust
    DUCK_TYPED = "duck_typed"  # Python, JavaScript


@dataclass
class TypeInfo:
    """Information about a type in a specific language."""

    name: str
    language: Language
    is_primitive: bool = False
    is_generic: bool = False
    generic_params: list[str] = field(default_factory=list)
    is_nullable: bool = False
    is_array: bool = False
    is_optional: bool = False
    is_tuple: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.name, self.language.value))


@dataclass
class TypeMapping:
    """
    Represents a mapping between types in different languages.

    Attributes:
        source_type: Type in source language
        target_type: Equivalent type in target language
        converter: Optional function to transform type expressions
        requires_import: Whether the mapping requires an import statement
        import_statement: The required import if any
        quality: Mapping quality (exact, close, approximate)
        notes: Additional notes about this mapping
    """

    source_type: str
    target_type: str
    requires_import: bool = False
    import_statement: str = ""
    quality: str = "exact"  # exact, close, approximate
    notes: str = ""

    def __post_init__(self) -> int:
        """Validate mapping quality."""
        valid_qualities = {"exact", "close", "approximate"}
        if self.quality not in valid_qualities:
            raise ValueError(f"Quality must be one of {valid_qualities}")

    @property
    def is_exact(self) -> bool:
        """Check if this is an exact type match."""
        return self.quality == "exact"

    @property
    def needs_review(self) -> bool:
        """Check if this mapping needs manual review."""
        return self.quality in {"close", "approximate"}


class TypeMapperProtocol(Protocol):
    """Protocol for type mapping implementations."""

    def map_type(self, source_type: str, target_lang: Language) -> TypeMapping:
        """Map a source type to the target language."""
        ...

    def get_imports(self, source_type: str) -> list[str]:
        """Get required imports for a type."""
        ...

    def supports_type(self, type_name: str) -> bool:
        """Check if this mapper supports a given type."""
        ...


class TypeMapper:
    """
    Main type mapping engine for Forge.

    Handles type conversions between all supported languages with
    awareness of each language's type system characteristics.
    """

    # Primitive type mappings: (source_lang, target_lang) -> {source_type: target_type}
    PRIMITIVE_MAPPINGS: dict[tuple[Language, Language], dict[str, str]] = {
        # TypeScript -> Python
        (Language.TYPESCRIPT, Language.PYTHON): {
            "number": "float | int",
            "string": "str",
            "boolean": "bool",
            "null": "None",
            "undefined": "None",
            "void": "None",
            "any": "Any",
            "never": "NoReturn",
            "unknown": "Any",
            "int": "int",
            "float": "float",
            "bigint": "int",
            "symbol": "str",
        },
        # TypeScript -> Rust
        (Language.TYPESCRIPT, Language.RUST): {
            "number": "f64",
            "string": "String",
            "boolean": "bool",
            "null": "()",
            "undefined": "Option<T>",
            "void": "()",
            "any": "serde_json::Value",
            "never": "!",
            "unknown": "serde_json::Value",
            "int": "i32",
            "float": "f64",
            "bigint": "i64",
            "symbol": "String",
        },
        # TypeScript -> Go
        (Language.TYPESCRIPT, Language.GO): {
            "number": "float64",
            "string": "string",
            "boolean": "bool",
            "null": "nil",
            "undefined": "nil",
            "void": "",
            "any": "interface{}",
            "never": "unreachable",
            "unknown": "interface{}",
            "int": "int",
            "float": "float64",
            "bigint": "int64",
            "symbol": "string",
        },
        # Python -> TypeScript
        (Language.PYTHON, Language.TYPESCRIPT): {
            "int": "number",
            "float": "number",
            "str": "string",
            "bool": "boolean",
            "None": "null",
            "bytes": "Uint8Array",
            "list": "Array<unknown>",
            "dict": "Record<string, unknown>",
            "tuple": "Array<unknown>",
            "set": "Set<unknown>",
            "frozenset": "ReadonlySet<unknown>",
            "type": "Function",
            "object": "object",
            "Any": "any",
            "Union": "unknown",
            "Optional": "T | null",
            "Literal": "never",
        },
        # Python -> Rust
        (Language.PYTHON, Language.RUST): {
            "int": "i64",
            "float": "f64",
            "str": "String",
            "bool": "bool",
            "None": "()",
            "bytes": "Vec<u8>",
            "list": "Vec<T>",
            "dict": "HashMap<String, T>",
            "tuple": "(T, U)",
            "set": "HashSet<T>",
            "frozenset": "HashSet<T>",
            "type": "fn()",
            "object": "serde_json::Value",
            "Any": "serde_json::Value",
        },
        # Python -> Go
        (Language.PYTHON, Language.GO): {
            "int": "int",
            "float": "float64",
            "str": "string",
            "bool": "bool",
            "None": "nil",
            "bytes": "[]byte",
            "list": "[]interface{}",
            "dict": "map[string]interface{}",
            "tuple": "struct{}",
            "set": "map[T]struct{}",
            "type": "interface{}",
            "object": "interface{}",
            "Any": "interface{}",
        },
        # Rust -> TypeScript
        (Language.RUST, Language.TYPESCRIPT): {
            "i8": "number",
            "i16": "number",
            "i32": "number",
            "i64": "bigint",
            "i128": "bigint",
            "isize": "number",
            "u8": "number",
            "u16": "number",
            "u32": "number",
            "u64": "bigint",
            "u128": "bigint",
            "usize": "number",
            "f32": "number",
            "f64": "number",
            "bool": "boolean",
            "char": "string",
            "str": "string",
            "String": "string",
            "()": "void",
            "!": "never",
        },
        # Rust -> Python
        (Language.RUST, Language.PYTHON): {
            "i8": "int",
            "i16": "int",
            "i32": "int",
            "i64": "int",
            "i128": "int",
            "isize": "int",
            "u8": "int",
            "u16": "int",
            "u32": "int",
            "u64": "int",
            "u128": "int",
            "usize": "int",
            "f32": "float",
            "f64": "float",
            "bool": "bool",
            "char": "str",
            "str": "str",
            "String": "str",
            "()": "None",
            "!": "NoReturn",
        },
        # Rust -> Go
        (Language.RUST, Language.GO): {
            "i8": "int8",
            "i16": "int16",
            "i32": "int32",
            "i64": "int64",
            "isize": "int",
            "u8": "uint8",
            "u16": "uint16",
            "u32": "uint32",
            "u64": "uint64",
            "usize": "uint",
            "f32": "float32",
            "f64": "float64",
            "bool": "bool",
            "char": "rune",
            "str": "string",
            "String": "string",
            "()": "",
        },
        # Go -> TypeScript
        (Language.GO, Language.TYPESCRIPT): {
            "int": "number",
            "int8": "number",
            "int16": "number",
            "int32": "number",
            "int64": "bigint",
            "uint": "number",
            "uint8": "number",
            "uint16": "number",
            "uint32": "number",
            "uint64": "bigint",
            "uintptr": "number",
            "float32": "number",
            "float64": "number",
            "complex64": "complex128",
            "complex128": "complex128",
            "bool": "boolean",
            "byte": "number",
            "rune": "string",
            "string": "string",
            "error": "Error",
            "any": "any",
            "interface{}": "any",
        },
        # Go -> Python
        (Language.GO, Language.PYTHON): {
            "int": "int",
            "int8": "int",
            "int16": "int",
            "int32": "int",
            "int64": "int",
            "uint": "int",
            "uint8": "int",
            "uint16": "int",
            "uint32": "int",
            "uint64": "int",
            "uintptr": "int",
            "float32": "float",
            "float64": "float",
            "complex64": "complex",
            "complex128": "complex",
            "bool": "bool",
            "byte": "int",
            "rune": "str",
            "string": "str",
            "error": "Exception",
            "any": "Any",
            "interface{}": "Any",
        },
        # Go -> Rust
        (Language.GO, Language.RUST): {
            "int": "c_int",
            "int8": "i8",
            "int16": "i16",
            "int32": "i32",
            "int64": "i64",
            "uint": "c_uint",
            "uint8": "u8",
            "uint16": "u16",
            "uint32": "u32",
            "uint64": "u64",
            "uintptr": "usize",
            "float32": "f32",
            "float64": "f64",
            "bool": "bool",
            "byte": "u8",
            "rune": "char",
            "string": "String",
            "error": "Box<dyn Error>",
            "any": "serde_json::Value",
            "interface{}": "serde_json::Value",
        },
    }

    def __init__(self) -> None:
        """Initialize the type mapper."""
        self._custom_mappings: dict[tuple[Language, Language], dict[str, TypeMapping]] = {}

    def map_type(
        self,
        source_type: str,
        source_lang: Language,
        target_lang: Language,
    ) -> TypeMapping:
        """
        Map a type from source language to target language.

        Args:
            source_type: The type name in source language
            source_lang: Source language
            target_lang: Target language

        Returns:
            TypeMapping with the equivalent type in target language
        """
        # Handle same language (no-op)
        if source_lang == target_lang:
            return TypeMapping(
                source_type=source_type,
                target_type=source_type,
                quality="exact",
            )

        # Handle generics
        if "<" in source_type:
            return self._map_generic_type(source_type, source_lang, target_lang)

        # Handle arrays
        if source_type.endswith("[]") or "Array<" in source_type:
            return self._map_array_type(source_type, source_lang, target_lang)

        # Handle optional/nullable types
        if "?" in source_type or "Optional[" in source_type:
            return self._map_optional_type(source_type, source_lang, target_lang)

        # Handle union types
        if " | " in source_type or "Union[" in source_type:
            return self._map_union_type(source_type, source_lang, target_lang)

        # Check custom mappings first
        custom_key = (source_lang, target_lang)
        if custom_key in self._custom_mappings:
            custom = self._custom_mappings[custom_key].get(source_type)
            if custom:
                return custom

        # Check primitive mappings
        mapping_key = (source_lang, target_lang)
        if mapping_key in self.PRIMITIVE_MAPPINGS:
            primitives = self.PRIMITIVE_MAPPINGS[mapping_key]
            if source_type in primitives:
                target_type = primitives[source_type]
                return TypeMapping(
                    source_type=source_type,
                    target_type=target_type,
                    quality="exact",
                    requires_import=target_type in {"Any", "NoReturn", "serde_json::Value"},
                    import_statement=self._get_type_import(target_type, target_lang),
                )

        # Unknown type - return as-is with approximation warning
        return TypeMapping(
            source_type=source_type,
            target_type=source_type,
            quality="approximate",
            notes=f"Type '{source_type}' could not be mapped - manual review recommended",
        )

    def _map_generic_type(
        self,
        source_type: str,
        source_lang: Language,
        target_lang: Language,
    ) -> TypeMapping:
        """Handle generic type mappings."""
        # Extract base type and type parameters
        base_type = source_type.split("<")[0]
        params_str = source_type[source_type.index("<") + 1 : source_type.rindex(">")]
        params = self._split_type_params(params_str)

        # Map each parameter
        mapped_params = []
        for param in params:
            mapping = self.map_type(param.strip(), source_lang, target_lang)
            mapped_params.append(mapping.target_type)

        # Convert syntax based on target language
        if target_lang == Language.PYTHON:
            target_type = f"{base_type}[{', '.join(mapped_params)}]"
        elif target_lang == Language.TYPESCRIPT:
            target_type = f"{base_type}<{', '.join(mapped_params)}>"
        elif target_lang == Language.RUST:
            target_type = f"{base_type}<{', '.join(mapped_params)}>"
        elif target_lang == Language.GO:
            # Go doesn't have generics syntax in older versions
            target_type = f"{base_type}[{', '.join(mapped_params)}]"
        else:
            target_type = source_type

        return TypeMapping(
            source_type=source_type,
            target_type=target_type,
            quality="close",
            notes="Generic type mapping - verify output",
        )

    def _map_array_type(
        self,
        source_type: str,
        source_lang: Language,
        target_lang: Language,
    ) -> TypeMapping:
        """Handle array type mappings."""
        # Extract element type
        if source_type.endswith("[]"):
            element_type = source_type[:-2]
        elif "Array<" in source_type:
            element_type = source_type[6:-1]
        else:
            element_type = "unknown"

        # Map element type
        element_mapping = self.map_type(element_type, source_lang, target_lang)

        # Convert array syntax
        if target_lang == Language.PYTHON:
            target_type = f"list[{element_mapping.target_type}]"
        elif target_lang == Language.TYPESCRIPT:
            target_type = f"{element_mapping.target_type}[]"
        elif target_lang == Language.RUST:
            target_type = f"Vec<{element_mapping.target_type}>"
        elif target_lang == Language.GO:
            target_type = f"[]{element_mapping.target_type}"

        return TypeMapping(
            source_type=source_type,
            target_type=target_type,
            quality=element_mapping.quality,
            requires_import=element_mapping.requires_import,
            import_statement=element_mapping.import_statement,
        )

    def _map_optional_type(
        self,
        source_type: str,
        source_lang: Language,
        target_lang: Language,
    ) -> TypeMapping:
        """Handle optional/nullable type mappings."""
        # Extract inner type
        if "?" in source_type:
            inner_type = source_type.replace("?", "").strip()
        elif "Optional[" in source_type:
            inner_type = source_type[8:-1]
        else:
            inner_type = source_type

        # Map inner type
        inner_mapping = self.map_type(inner_type, source_lang, target_lang)

        # Convert optional syntax
        if target_lang == Language.PYTHON:
            target_type = f"Optional[{inner_mapping.target_type}]"
            requires_import = True
            import_stmt = "from typing import Optional"
        elif target_lang == Language.TYPESCRIPT:
            target_type = f"{inner_mapping.target_type} | null"
        elif target_lang == Language.RUST:
            target_type = f"Option<{inner_mapping.target_type}>"
        elif target_lang == Language.GO:
            target_type = f"*{inner_mapping.target_type}"

        return TypeMapping(
            source_type=source_type,
            target_type=target_type,
            quality=inner_mapping.quality,
            requires_import=requires_import,
            import_statement=import_stmt if target_lang == Language.PYTHON else "",
        )

    def _map_union_type(
        self,
        source_type: str,
        source_lang: Language,
        target_lang: Language,
    ) -> TypeMapping:
        """Handle union type mappings."""
        # Extract union members
        if " | " in source_type:
            members = [m.strip() for m in source_type.split("|")]
        elif "Union[" in source_type:
            members = source_type[6:-1].split(", ")
        else:
            members = [source_type]

        # Map each member
        mapped_members = []
        imports_needed: list[str] = []
        for member in members:
            mapping = self.map_type(member, source_lang, target_lang)
            mapped_members.append(mapping.target_type)
            if mapping.requires_import and mapping.import_statement:
                imports_needed.append(mapping.import_statement)

        # Convert union syntax
        if target_lang == Language.PYTHON:
            if len(mapped_members) == 2 and "None" in mapped_members:
                # Convert to Optional
                non_none = [m for m in mapped_members if m != "None"][0]
                target_type = f"Optional[{non_none}]"
            else:
                target_type = f"Union[{', '.join(mapped_members)}]"
            import_stmt = "from typing import Union" + ("Optional" if "Optional" in target_type else "")
        elif target_lang == Language.TYPESCRIPT:
            target_type = " | ".join(mapped_members)
            import_stmt = ""
        elif target_lang == Language.RUST:
            target_type = "Result<" + ", ".join(mapped_members) + ">"
            import_stmt = ""
        elif target_lang == Language.GO:
            target_type = "interface{}"
            import_stmt = ""

        return TypeMapping(
            source_type=source_type,
            target_type=target_type,
            quality="close",
            requires_import=bool(imports_needed),
            import_statement=", ".join(set(imports_needed)),
        )

    def _split_type_params(self, params_str: str) -> list[str]:
        """Split type parameters, respecting nested generics."""
        params: list[str] = []
        current = ""
        depth = 0

        for char in params_str:
            if char in {"<", "[", "("}:
                depth += 1
                current += char
            elif char in {">", "]", ")"}:
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                params.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            params.append(current.strip())

        return params

    def _get_type_import(self, type_name: str, target_lang: Language) -> str:
        """Get the import statement for a type."""
        imports = {
            Language.PYTHON: {
                "Any": "from typing import Any",
                "NoReturn": "from typing import NoReturn",
            },
            Language.RUST: {
                "serde_json::Value": "use serde_json;",
            },
        }
        lang_imports = imports.get(target_lang, {})
        return lang_imports.get(type_name, "")

    def add_custom_mapping(
        self,
        source_type: str,
        target_type: str,
        source_lang: Language,
        target_lang: Language,
        quality: str = "exact",
    ) -> None:
        """
        Add a custom type mapping.

        Args:
            source_type: Type in source language
            target_type: Equivalent type in target language
            source_lang: Source language
            target_lang: Target language
            quality: Mapping quality (exact, close, approximate)
        """
        key = (source_lang, target_lang)
        if key not in self._custom_mappings:
            self._custom_mappings[key] = {}

        self._custom_mappings[key][source_type] = TypeMapping(
            source_type=source_type,
            target_type=target_type,
            quality=quality,
        )

    def get_imports_for_mapping(
        self,
        mappings: list[TypeMapping],
    ) -> list[str]:
        """Get deduplicated list of required imports from mappings."""
        imports: set[str] = set()
        for mapping in mappings:
            if mapping.requires_import and mapping.import_statement:
                imports.add(mapping.import_statement)
        return sorted(list(imports))
