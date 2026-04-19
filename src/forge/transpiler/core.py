"""
Core transpiler engine for Forge.

Provides the main transpilation functionality combining AST parsing,
type mapping, and LLM-assisted translation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from forge.llm.llm_config import LLMConfig
from forge.llm.llm_translator import LLMTranslator
from forge.parsers.base import ASTNode, ParseResult, ProgramNode
from forge.parsers.typescript_parser import TypeScriptParser
from forge.parsers.python_parser import PythonParser
from forge.parsers.rust_parser import RustParser
from forge.parsers.go_parser import GoParser
from forge.transpiler.language import Language, LanguagePair, get_language_pair
from forge.types.type_mapper import TypeMapper


@dataclass
class TranspilerConfig:
    """
    Configuration for the transpiler.

    Attributes:
        source_language: Source language
        target_language: Target language
        use_llm: Whether to use LLM assistance
        llm_config: LLM configuration
        preserve_comments: Preserve comments in output
        preserve_formatting: Attempt to preserve formatting
        add_header: Add header comment with translation info
        verify_output: Verify the output compiles
        strict_types: Use strict type checking
    """

    source_language: Language
    target_language: Language
    use_llm: bool = False
    llm_config: Optional[LLMConfig] = None
    preserve_comments: bool = True
    preserve_formatting: bool = True
    add_header: bool = True
    verify_output: bool = True
    strict_types: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.source_language == self.target_language:
            raise ValueError("Source and target languages must be different")


@dataclass
class TranspileResult:
    """
    Result of a transpilation operation.

    Attributes:
        success: Whether transpilation succeeded
        output: The transpiled code
        source_language: Source language
        target_language: Target language
        errors: Any errors encountered
        warnings: Any warnings
        metrics: Transpilation metrics
        ast: The parsed AST (if available)
    """

    success: bool
    output: str
    source_language: Language
    target_language: Language
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    ast: Optional[ProgramNode] = None

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there were any warnings."""
        return len(self.warnings) > 0

    def __str__(self) -> str:
        """String representation of the result."""
        status = "Success" if self.success else "Failed"
        parts = [f"Transpilation {status}"]
        parts.append(f"({self.source_language.display_name} -> {self.target_language.display_name})")

        if self.has_errors:
            parts.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                parts.append(f"  - {error}")

        if self.has_warnings:
            parts.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                parts.append(f"  - {warning}")

        if self.metrics:
            parts.append("\nMetrics:")
            for key, value in self.metrics.items():
                parts.append(f"  {key}: {value}")

        return "\n".join(parts)


class Transpiler:
    """
    Main transpiler engine.

    Combines AST parsing, type mapping, and LLM assistance to
    convert code between programming languages.
    """

    # Language-specific code generators
    CODE_GENERATORS: dict[Language, Callable[[ASTNode], str]] = {}

    def __init__(self, config: Optional[TranspilerConfig] = None) -> None:
        """
        Initialize the transpiler.

        Args:
            config: Transpiler configuration
        """
        self.config = config or TranspilerConfig(
            source_language=Language.TYPESCRIPT,
            target_language=Language.PYTHON,
        )

        # Initialize components
        self.type_mapper = TypeMapper()
        self._parsers = self._init_parsers()
        self._llm_translator: Optional[LLMTranslator] = None

        if self.config.use_llm:
            llm_config = self.config.llm_config or LLMConfig.from_env()
            self._llm_translator = LLMTranslator(llm_config)

    def _init_parsers(self) -> dict[Language, Any]:
        """Initialize language parsers."""
        return {
            Language.TYPESCRIPT: TypeScriptParser(),
            Language.PYTHON: PythonParser(),
            Language.RUST: RustParser(),
            Language.GO: GoParser(),
        }

    def transpile(self, source_code: str) -> TranspileResult:
        """
        Transpile source code from source language to target language.

        Args:
            source_code: The source code to transpile

        Returns:
            TranspileResult containing the output and metadata
        """
        import time

        start_time = time.time()
        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Step 1: Parse source code
            parse_result = self._parse(source_code)
            if not parse_result.success:
                return TranspileResult(
                    success=False,
                    output="",
                    source_language=self.config.source_language,
                    target_language=self.config.target_language,
                    errors=[str(e) for e in parse_result.errors],
                    warnings=[str(w) for w in parse_result.warnings],
                )

            ast = parse_result.ast
            if not ast:
                return TranspileResult(
                    success=False,
                    output="",
                    source_language=self.config.source_language,
                    target_language=self.config.target_language,
                    errors=["Failed to parse source code"],
                )

            # Step 2: Generate code for target language
            if self.config.use_llm and self._llm_translator:
                # Use LLM for translation
                import asyncio

                output = asyncio.run(
                    self._llm_translator.translate(
                        source_code=source_code,
                        source_lang=self.config.source_language.display_name,
                        target_lang=self.config.target_language.display_name,
                    )
                )
            else:
                # Use AST-based translation
                output = self._generate_code(ast)

            # Step 3: Post-process output
            output = self._post_process(output)

            # Calculate metrics
            elapsed = time.time() - start_time
            metrics = {
                "elapsed_seconds": round(elapsed, 3),
                "source_lines": len(source_code.splitlines()),
                "output_lines": len(output.splitlines()),
                "language_pair": get_language_pair(
                    self.config.source_language, self.config.target_language
                ).key,
            }

            return TranspileResult(
                success=True,
                output=output,
                source_language=self.config.source_language,
                target_language=self.config.target_language,
                warnings=warnings,
                metrics=metrics,
                ast=ast,
            )

        except Exception as e:
            errors.append(str(e))
            return TranspileResult(
                success=False,
                output="",
                source_language=self.config.source_language,
                target_language=self.config.target_language,
                errors=errors,
            )

    def _parse(self, source_code: str) -> ParseResult:
        """Parse source code into an AST."""
        parser = self._parsers.get(self.config.source_language)
        if not parser:
            return ParseResult(
                success=False,
                errors=[],
                source_code=source_code,
                language=self.config.source_language,
            )

        return parser.parse(source_code)

    def _generate_code(self, ast: ProgramNode) -> str:
        """Generate code from AST for target language."""
        generator = CodeGenerator(
            target_language=self.config.target_language,
            type_mapper=self.type_mapper,
            config=self.config,
        )
        return generator.generate(ast)

    def _post_process(self, code: str) -> str:
        """Post-process generated code."""
        lines = code.splitlines()

        # Add header if requested
        if self.config.add_header:
            header = self._generate_header()
            lines = [header, ""] + lines

        # Normalize line endings
        code = "\n".join(lines)

        # Remove excessive blank lines
        if not self.config.preserve_formatting:
            code = re.sub(r"\n{3,}", "\n\n", code)

        return code.strip() + "\n"

    def _generate_header(self) -> str:
        """Generate a header comment for the output file."""
        pair = get_language_pair(self.config.source_language, self.config.target_language)

        header_lines = [
            f"// Generated by Forge transpiler",
            f"// Source: {self.config.source_language.display_name}",
            f"// Target: {self.config.target_language.display_name}",
            f"// Difficulty: {pair.difficulty}/5",
            "",
        ]

        if self.config.preserve_comments:
            header_lines.append("// Comments have been preserved from the original source")
        else:
            header_lines.append("// Note: Comments were not preserved during transpilation")

        if pair.notes:
            header_lines.append(f"// Note: {pair.notes}")

        return "\n".join(header_lines)


class CodeGenerator:
    """
    Code generator for translating AST to target language.

    Converts our intermediate AST representation to language-specific code.
    """

    def __init__(
        self,
        target_language: Language,
        type_mapper: TypeMapper,
        config: TranspilerConfig,
    ) -> None:
        """
        Initialize the code generator.

        Args:
            target_language: Target language for generation
            type_mapper: Type mapper instance
            config: Transpiler configuration
        """
        self.target_language = target_language
        self.type_mapper = type_mapper
        self.config = config
        self._indent_level = 0
        self._indent_str = "    "

    def generate(self, ast: ProgramNode) -> str:
        """
        Generate code from AST.

        Args:
            ast: The AST to generate code from

        Returns:
            Generated code string
        """
        lines = []

        for node in ast.body:
            generated = self._generate_node(node)
            if generated:
                lines.append(generated)

        return "\n".join(lines)

    def _generate_node(self, node: ASTNode) -> str:
        """Generate code for a single AST node."""
        from forge.parsers.base import (
            FunctionDeclarationNode,
            ClassDeclarationNode,
            VariableDeclarationNode,
            IfStatementNode,
            ForLoopNode,
            WhileLoopNode,
            ReturnStatementNode,
            CallNode,
            BinaryOpNode,
            UnaryOpNode,
            IdentifierNode,
            LiteralNode,
            MemberAccessNode,
            ArrayLiteralNode,
            ObjectLiteralNode,
            LambdaNode,
            BlockNode,
            ImportNode,
            ExportNode,
            MatchStatementNode,
            TryStatementNode,
            ParameterNode,
        )

        handlers = {
            FunctionDeclarationNode: self._generate_function,
            ClassDeclarationNode: self._generate_class,
            VariableDeclarationNode: self._generate_variable,
            IfStatementNode: self._generate_if,
            ForLoopNode: self._generate_for,
            WhileLoopNode: self._generate_while,
            ReturnStatementNode: self._generate_return,
            CallNode: self._generate_call,
            BinaryOpNode: self._generate_binary_op,
            UnaryOpNode: self._generate_unary_op,
            IdentifierNode: self._generate_identifier,
            LiteralNode: self._generate_literal,
            MemberAccessNode: self._generate_member_access,
            ArrayLiteralNode: self._generate_array,
            ObjectLiteralNode: self._generate_object,
            LambdaNode: self._generate_lambda,
            BlockNode: self._generate_block,
            ImportNode: self._generate_import,
            ExportNode: self._generate_export,
            MatchStatementNode: self._generate_match,
            TryStatementNode: self._generate_try,
        }

        handler = handlers.get(type(node))
        if handler:
            return handler(node)

        # Fallback: use source code if available
        return node.source if hasattr(node, "source") else ""

    def _generate_function(self, node: FunctionDeclarationNode) -> str:
        """Generate function declaration."""
        params = ", ".join(self._generate_node(p) for p in node.parameters)
        body = self._generate_node(node.body) if node.body else "{}"

        if self.target_language == Language.PYTHON:
            async_prefix = "async " if node.is_async else ""
            type_hint = f" -> {node.return_type.type_name}" if node.return_type else ""
            return f"def {node.name}({params}){type_hint}:\n{body}\n"

        elif self.target_language == Language.TYPESCRIPT:
            async_prefix = "async " if node.is_async else ""
            type_hint = f": {node.return_type.type_name}" if node.return_type else ""
            return f"function {node.name}({params}){type_hint} {body}"

        elif self.target_language == Language.RUST:
            async_prefix = "async " if node.is_async else ""
            type_hint = f" -> {node.return_type.type_name}" if node.return_type else ""
            return f"fn {node.name}({params}){type_hint} {body}"

        elif self.target_language == Language.GO:
            type_hint = f" {node.return_type.type_name}" if node.return_type else ""
            return f"func {node.name}({params}){type_hint} {body}"

        return f"function {node.name}({params}) {body}"

    def _generate_class(self, node: ClassDeclarationNode) -> str:
        """Generate class declaration."""
        base = ""
        if node.base_classes:
            if self.target_language == Language.PYTHON:
                base = f"({', '.join(node.base_classes)})"
            elif self.target_language == Language.TYPESCRIPT:
                base = f" extends {node.base_classes[0]}"
            elif self.target_language == Language.GO:
                base = ""

        body_lines = []
        for member in node.body:
            body_lines.append(self._generate_node(member))

        body = "\n".join(body_lines)

        if self.target_language == Language.PYTHON:
            return f"class {node.name}{base}:\n{body}\n"
        elif self.target_language == Language.TYPESCRIPT:
            return f"class {node.name}{base} {{\n{body}\n}}"
        elif self.target_language == Language.RUST:
            return f"struct {node.name} {{\n{body}\n}}"
        elif self.target_language == Language.GO:
            return f"type {node.name} struct {{\n{body}\n}}"

        return f"class {node.name}{base} {{\n{body}\n}}"

    def _generate_variable(self, node: VariableDeclarationNode) -> str:
        """Generate variable declaration."""
        type_hint = ""
        if node.variable_type:
            type_hint = self.type_mapper.map_type(
                node.variable_type.type_name,
                node.language,
                self.target_language,
            ).target_type

        initializer = ""
        if node.initializer:
            initializer = f" = {self._generate_node(node.initializer)}"

        if self.target_language == Language.PYTHON:
            if type_hint:
                type_hint = f": {type_hint}"
            const_prefix = ""  # Python uses different conventions
            return f"{const_prefix}{node.name}{type_hint}{initializer}"

        elif self.target_language == Language.TYPESCRIPT:
            if type_hint:
                type_hint = f": {type_hint}"
            const_prefix = "const " if node.is_constant else "let "
            return f"{const_prefix}{node.name}{type_hint}{initializer};"

        elif self.target_language == Language.RUST:
            if type_hint:
                type_hint = f": {type_hint}"
            const_prefix = "const " if node.is_constant else "let "
            immutability = "" if node.is_constant else "mut "
            return f"{const_prefix}{immutability}{node.name}{type_hint}{initializer};"

        elif self.target_language == Language.GO:
            if type_hint:
                type_hint = f" {type_hint}"
            return f"var {node.name}{type_hint}{initializer}"

        return f"{node.name}{type_hint}{initializer}"

    def _generate_if(self, node: Any) -> str:
        """Generate if statement."""
        condition = self._generate_node(node.condition)
        consequent = self._generate_node(node.consequent)

        lines = [f"if ({condition}) {{", consequent, "}"]

        if node.alternate:
            alternate = self._generate_node(node.alternate)
            lines.append("else {")
            lines.append(alternate)
            lines.append("}")

        return "\n".join(lines)

    def _generate_for(self, node: Any) -> str:
        """Generate for loop."""
        if self.target_language == Language.PYTHON:
            init = self._generate_node(node.initializer) if node.initializer else ""
            cond = self._generate_node(node.condition) if node.condition else ""
            update = self._generate_node(node.update) if node.update else ""
            body = self._generate_node(node.body) if node.body else "pass"

            if init and cond and update:
                return f"for {init}; {cond}; {update}:\n{body}\n"
            return f"for {init} in {cond}:\n{body}\n"

        else:
            init = self._generate_node(node.initializer) if node.initializer else ""
            cond = self._generate_node(node.condition) if node.condition else ""
            update = self._generate_node(node.update) if node.update else ""
            body = self._generate_node(node.body) if node.body else "{}"

            return f"for ({init}; {cond}; {update}) {{ {body} }}"

    def _generate_while(self, node: Any) -> str:
        """Generate while loop."""
        condition = self._generate_node(node.condition)
        body = self._generate_node(node.body) if node.body else "{}"

        if self.target_language == Language.PYTHON:
            return f"while {condition}:\n{body}\n"
        return f"while ({condition}) {{ {body} }}"

    def _generate_return(self, node: Any) -> str:
        """Generate return statement."""
        if node.argument:
            value = self._generate_node(node.argument)
            if self.target_language == Language.PYTHON:
                return f"return {value}"
            return f"return {value};"
        if self.target_language == Language.PYTHON:
            return "return"
        return "return;"

    def _generate_call(self, node: Any) -> str:
        """Generate function call."""
        callee = self._generate_node(node.callee)
        args = ", ".join(self._generate_node(arg) for arg in node.arguments)
        return f"{callee}({args})"

    def _generate_binary_op(self, node: Any) -> str:
        """Generate binary operation."""
        left = self._generate_node(node.left)
        right = self._generate_node(node.right)
        return f"({left} {node.operator} {right})"

    def _generate_unary_op(self, node: Any) -> str:
        """Generate unary operation."""
        operand = self._generate_node(node.operand)
        if node.is_postfix:
            return f"{operand}{node.operator}"
        return f"{node.operator}{operand}"

    def _generate_identifier(self, node: Any) -> str:
        """Generate identifier."""
        return node.name

    def _generate_literal(self, node: Any) -> str:
        """Generate literal value."""
        return node.raw_value

    def _generate_member_access(self, node: Any) -> str:
        """Generate member access."""
        obj = self._generate_node(node.object)
        if node.is_safe:
            return f"{obj}?.{node.property_name}"
        return f"{obj}.{node.property_name}"

    def _generate_array(self, node: Any) -> str:
        """Generate array literal."""
        elements = ", ".join(self._generate_node(el) for el in node.elements)
        return f"[{elements}]"

    def _generate_object(self, node: Any) -> str:
        """Generate object literal."""
        props = []
        for prop in node.properties:
            key = self._generate_node(prop.key)
            if prop.value:
                value = self._generate_node(prop.value)
                if prop.shorthand:
                    props.append(key)
                else:
                    props.append(f"{key}: {value}")
            else:
                props.append(key)

        return "{" + ", ".join(props) + "}"

    def _generate_lambda(self, node: Any) -> str:
        """Generate lambda/arrow function."""
        params = ", ".join(self._generate_node(p) for p in node.parameters)
        body = self._generate_node(node.body) if node.body else "{}"

        if self.target_language == Language.PYTHON:
            return f"lambda {params}: {body}"
        return f"({params}) => {body}"

    def _generate_block(self, node: Any) -> str:
        """Generate block."""
        self._indent_level += 1
        lines = []
        for stmt in node.statements:
            indent = self._indent_str * self._indent_level
            lines.append(f"{indent}{self._generate_node(stmt)}")
        self._indent_level -= 1

        if self.target_language == Language.PYTHON:
            return "\n".join(lines) + "\n"
        return "{\n" + "\n".join(lines) + "\n}"

    def _generate_import(self, node: Any) -> str:
        """Generate import statement."""
        if self.target_language == Language.PYTHON:
            if node.imported_names:
                names = ", ".join(node.imported_names)
                return f"from {node.module_name} import {names}"
            return f"import {node.module_name}"

        elif self.target_language == Language.TYPESCRIPT:
            if node.is_namespace:
                alias = node.alias or "namespace"
                return f"import * as {alias} from '{node.module_name}';"
            if node.is_default:
                name = node.imported_names[0] if node.imported_names else "default"
                alias = f" as {node.alias}" if node.alias else ""
                return f"import {name}{alias} from '{node.module_name}';"
            names = ", ".join(node.imported_names)
            return f"import {{{names}}} from '{node.module_name}';"

        elif self.target_language == Language.GO:
            if node.alias:
                return f"import {node.alias} \"{node.module_name}\""
            return f"import \"{node.module_name}\""

        elif self.target_language == Language.RUST:
            if node.imported_names:
                names = ", ".join(node.imported_names)
                return f"use {node.module_name}::{{{names}}};"
            return f"use {node.module_name};"

        return f"import {node.module_name};"

    def _generate_export(self, node: Any) -> str:
        """Generate export statement."""
        if self.target_language in {Language.TYPESCRIPT, Language.JAVASCRIPT}:
            if node.is_default:
                return f"export default {node.exported_name};"
            return f"export {node.exported_name};"

        elif self.target_language == Language.PYTHON:
            return f"export {node.exported_name}"  # Python uses __all__

        elif self.target_language == Language.GO:
            # Go doesn't have exports, just capitalize
            return f"// exported: {node.exported_name}"

        return f"export {node.exported_name};"

    def _generate_match(self, node: Any) -> str:
        """Generate match/switch statement."""
        expr = self._generate_node(node.expression)
        cases = []

        for case in node.cases:
            pattern = self._generate_node(case.pattern)
            body = self._generate_node(case.body) if case.body else "{}"
            cases.append(f"case {pattern}: {body}")

        if self.target_language == Language.PYTHON:
            return f"match {expr}:\n" + "\n".join(f"    {c}" for c in cases) + "\n"

        return f"switch ({expr}) {{\n" + "\n".join(cases) + "\n}}"

    def _generate_try(self, node: Any) -> str:
        """Generate try/catch statement."""
        block = self._generate_node(node.block) if node.block else "{}"
        parts = [f"try {{ {block} }}"]

        if node.handler:
            handler = node.handler
            param = f"({handler.parameter})" if handler.parameter else ""
            body = self._generate_node(handler.body) if handler.body else "{}"
            parts.append(f"catch {param} {{ {body} }}")

        if node.finalizer:
            fin = self._generate_node(node.finalizer)
            parts.append(f"finally {{ {fin} }}")

        return " ".join(parts)
