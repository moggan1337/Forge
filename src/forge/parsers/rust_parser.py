"""
Rust parser using tree-sitter.

Provides AST parsing for Rust source code.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    from tree_sitter_languages import get_parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from forge.parsers.base import (
    ArrayLiteralNode,
    ASTNode,
    BinaryOpNode,
    BlockNode,
    CallNode,
    CatchClauseNode,
    ClassDeclarationNode,
    Documentation,
    ExportNode,
    ForLoopNode,
    FunctionDeclarationNode,
    IdentifierNode,
    IfStatementNode,
    ImportNode,
    LambdaNode,
    LiteralNode,
    MatchCaseNode,
    MatchStatementNode,
    MemberAccessNode,
    ObjectLiteralNode,
    ParameterNode,
    ParseError,
    ParseResult,
    ParseWarning,
    ProgramNode,
    PropertyNode,
    ReturnStatementNode,
    TryStatementNode,
    TypeAnnotation,
    UnaryOpNode,
    VariableDeclarationNode,
    WhileLoopNode,
)
from forge.transpiler.language import Language


class RustParser:
    """
    Parser for Rust source code.

    Uses tree-sitter for parsing when available.
    """

    def __init__(self) -> None:
        """Initialize the Rust parser."""
        self._parser = None
        if TREE_SITTER_AVAILABLE:
            self._parser = get_parser("rust")

    @property
    def language(self) -> Language:
        """Get the language this parser handles."""
        return Language.RUST

    def parse(self, source_code: str) -> ParseResult:
        """
        Parse Rust source code into an AST.

        Args:
            source_code: The Rust source code to parse

        Returns:
            ParseResult containing the AST and any errors/warnings
        """
        if not TREE_SITTER_AVAILABLE:
            return self._parse_fallback(source_code)

        try:
            tree = self._parser.parse(source_code.encode())
            errors: list[ParseError] = []
            warnings: list[ParseWarning] = []

            # Check for parse errors
            self._collect_errors(tree.root_node, source_code, errors, warnings)

            # Convert to our AST format
            ast = self._convert_node(tree.root_node, source_code)
            if ast:
                ast.source_code = source_code

            return ParseResult(
                success=len(errors) == 0,
                ast=ast,
                errors=errors,
                warnings=warnings,
                source_code=source_code,
                language=Language.RUST,
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[ParseError(message=str(e), line=1, column=0)],
                source_code=source_code,
                language=Language.RUST,
            )

    def _parse_fallback(self, source_code: str) -> ParseResult:
        """Fallback parser for when tree-sitter is not available."""
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = [
            ParseWarning(
                message="Using fallback parser - tree-sitter not available. Results may be incomplete.",
                line=1,
                column=0,
            )
        ]

        statements: list[ASTNode] = []
        lines = source_code.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Create basic identifier nodes
            if stripped:
                statements.append(
                    IdentifierNode(
                        name=stripped[:50],
                        source_code=stripped,
                        language=Language.RUST,
                    )
                )

        program = ProgramNode(
            body=statements,
            language=Language.RUST,
            source_code=source_code,
        )

        return ParseResult(
            success=True,
            ast=program,
            errors=errors,
            warnings=warnings,
            source_code=source_code,
            language=Language.RUST,
        )

    def _collect_errors(
        self,
        node: Any,
        source: str,
        errors: list[ParseError],
        warnings: list[ParseWarning],
    ) -> None:
        """Recursively collect parse errors from the tree."""
        if hasattr(node, "type") and node.type == "ERROR":
            start = node.start_point
            errors.append(
                ParseError(
                    message=f"Parse error: {node.text.decode()[:50] if hasattr(node, 'text') else 'unknown'}",
                    line=start[0] + 1,
                    column=start[1],
                )
            )

        if hasattr(node, "children"):
            for child in node.children:
                self._collect_errors(child, source, errors, warnings)

    def _convert_node(self, node: Any, source: str) -> Optional[ProgramNode]:
        """Convert a tree-sitter node to our AST format."""
        if node.type == "source_file":
            body = []
            for child in node.children:
                converted = self._convert_item(child, source)
                if converted:
                    body.append(converted)
            return ProgramNode(body=body, language=Language.RUST, source_code=source)

        return None

    def _convert_item(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert a source file item."""
        converters = {
            "function_item": self._convert_function_item,
            "struct_item": self._convert_struct_item,
            "enum_item": self._convert_enum_item,
            "impl_item": self._convert_impl_item,
            "trait_item": self._convert_trait_item,
            "let_declaration": self._convert_let,
            "let_binding": self._convert_let_binding,
            "use_declaration": self._convert_use,
            "mod_item": self._convert_mod,
            "const_item": self._convert_const,
            "static_item": self._convert_static,
            "type_alias_item": self._convert_type_alias,
        }

        converter = converters.get(node.type)
        if converter:
            return converter(node, source)

        # Try to convert as a statement
        return self._convert_statement(node, source)

    def _convert_function_item(self, node: Any, source: str) -> FunctionDeclarationNode:
        """Convert a function item."""
        name = ""
        parameters: list[ParameterNode] = []
        body: Optional[BlockNode] = None
        return_type: Optional[TypeAnnotation] = None

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "parameters":
                parameters = self._convert_parameters(child, source)
            elif child.type == "block":
                body = self._convert_block(child, source)
            elif child.type == "type_identifier":
                # Return type
                pass

        return FunctionDeclarationNode(
            name=name,
            parameters=parameters,
            body=body,
            return_type=return_type,
            language=Language.RUST,
        )

    def _convert_struct_item(self, node: Any, source: str) -> ClassDeclarationNode:
        """Convert a struct item."""
        name = ""
        body: list[ASTNode] = []

        for child in node.children:
            if child.type == "identifier" or child.type == "type_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "field_declaration_list":
                for field in child.children:
                    if field.type == "field_declaration":
                        body.append(self._convert_field_declaration(field, source))

        return ClassDeclarationNode(
            name=name,
            body=body,
            language=Language.RUST,
        )

    def _convert_enum_item(self, node: Any, source: str) -> ClassDeclarationNode:
        """Convert an enum item."""
        name = ""
        body: list[ASTNode] = []

        for child in node.children:
            if child.type == "identifier" or child.type == "type_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "variant_list":
                for variant in child.children:
                    if variant.type == "enum_variant":
                        body.append(self._convert_enum_variant(variant, source))

        return ClassDeclarationNode(
            name=f"enum {name}",
            body=body,
            language=Language.RUST,
        )

    def _convert_impl_item(self, node: Any, source: str) -> ClassDeclarationNode:
        """Convert an impl item."""
        name = "impl"
        body: list[ASTNode] = []

        for child in node.children:
            if child.type == "block":
                body = self._convert_body(child, source)
            elif child.type == "type_identifier":
                name = f"impl {child.text.decode()}" if hasattr(child, "text") else "impl"

        return ClassDeclarationNode(
            name=name,
            body=body,
            language=Language.RUST,
        )

    def _convert_trait_item(self, node: Any, source: str) -> ClassDeclarationNode:
        """Convert a trait item."""
        name = ""
        body: list[ASTNode] = []

        for child in node.children:
            if child.type == "identifier" or child.type == "type_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "declaration_list":
                for decl in child.children:
                    body.append(self._convert_statement(decl, source))

        return ClassDeclarationNode(
            name=f"trait {name}",
            body=body,
            language=Language.RUST,
        )

    def _convert_let(self, node: Any, source: str) -> VariableDeclarationNode:
        """Convert a let declaration."""
        name = ""
        var_type: Optional[TypeAnnotation] = None
        initializer: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "type_annotation":
                var_type = self._convert_type_annotation(child, source)
            elif child.type in {"integer", "float", "string", "boolean", "identifier"}:
                initializer = self._convert_expression(child, source)

        return VariableDeclarationNode(
            name=name,
            variable_type=var_type,
            initializer=initializer,
            language=Language.RUST,
        )

    def _convert_let_binding(self, node: Any, source: str) -> VariableDeclarationNode:
        """Convert a let binding pattern."""
        return self._convert_let(node, source)

    def _convert_use(self, node: Any, source: str) -> ImportNode:
        """Convert a use declaration."""
        path = ""

        for child in node.children:
            if child.type in {"primitive_type", "type_identifier", "identifier", "scoped_identifier"}:
                path = child.text.decode() if hasattr(child, "text") else str(child)

        return ImportNode(
            module_name=path,
            imported_names=[],
            language=Language.RUST,
        )

    def _convert_mod(self, node: Any, source: str) -> IdentifierNode:
        """Convert a mod declaration."""
        name = ""
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
        return IdentifierNode(name=f"mod {name}", language=Language.RUST)

    def _convert_const(self, node: Any, source: str) -> VariableDeclarationNode:
        """Convert a const declaration."""
        name = ""
        value: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type in {"integer", "float", "string", "boolean"}:
                value = self._convert_literal(child, source)

        return VariableDeclarationNode(
            name=name,
            initializer=value,
            is_constant=True,
            language=Language.RUST,
        )

    def _convert_static(self, node: Any, source: str) -> VariableDeclarationNode:
        """Convert a static declaration."""
        return self._convert_const(node, source)

    def _convert_type_alias(self, node: Any, source: str) -> IdentifierNode:
        """Convert a type alias."""
        name = ""
        alias_type = ""

        for child in node.children:
            if child.type == "type_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "type_identifier" or child.type == "primitive_type":
                alias_type = child.text.decode() if hasattr(child, "text") else str(child)

        return IdentifierNode(name=f"type {name} = {alias_type}", language=Language.RUST)

    def _convert_statement(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert a statement."""
        converters = {
            "let_declaration": self._convert_let,
            "expression_statement": self._convert_expression_statement,
            "return_expression": self._convert_return,
            "block": self._convert_block,
        }

        converter = converters.get(node.type)
        if converter:
            return converter(node, source)

        return self._convert_expression(node, source)

    def _convert_expression_statement(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert an expression statement."""
        for child in node.children:
            if child.is_named:
                return self._convert_expression(child, source)
        return None

    def _convert_return(self, node: Any, source: str) -> ReturnStatementNode:
        """Convert a return expression."""
        argument: Optional[ASTNode] = None

        for child in node.children:
            if child.is_named:
                argument = self._convert_expression(child, source)

        return ReturnStatementNode(argument=argument, language=Language.RUST)

    def _convert_block(self, node: Any, source: str) -> BlockNode:
        """Convert a block."""
        statements = []
        for child in node.children:
            converted = self._convert_statement(child, source)
            if converted:
                statements.append(converted)
        return BlockNode(statements=statements, language=Language.RUST)

    def _convert_body(self, node: Any, source: str) -> list[ASTNode]:
        """Convert a body (statements inside a block)."""
        statements = []
        for child in node.children:
            converted = self._convert_statement(child, source)
            if converted:
                statements.append(converted)
        return statements

    def _convert_parameters(self, node: Any, source: str) -> list[ParameterNode]:
        """Convert function parameters."""
        parameters = []
        for child in node.children:
            if child.type == "parameter":
                parameters.append(self._convert_parameter(child, source))
        return parameters

    def _convert_parameter(self, node: Any, source: str) -> ParameterNode:
        """Convert a single parameter."""
        name = ""
        param_type: Optional[TypeAnnotation] = None

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "type_annotation":
                param_type = self._convert_type_annotation(child, source)

        return ParameterNode(name=name, parameter_type=param_type, language=Language.RUST)

    def _convert_field_declaration(self, node: Any, source: str) -> VariableDeclarationNode:
        """Convert a field declaration."""
        name = ""
        field_type: Optional[TypeAnnotation] = None

        for child in node.children:
            if child.type == "identifier" or child.type == "field_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "type_annotation":
                field_type = self._convert_type_annotation(child, source)

        return VariableDeclarationNode(name=name, variable_type=field_type, language=Language.RUST)

    def _convert_enum_variant(self, node: Any, source: str) -> IdentifierNode:
        """Convert an enum variant."""
        name = ""
        for child in node.children:
            if child.type == "identifier" or child.type == "type_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
        return IdentifierNode(name=name, language=Language.RUST)

    def _convert_expression(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert an expression."""
        converters = {
            "identifier": self._convert_identifier,
            "integer": self._convert_integer,
            "float": self._convert_float,
            "string": self._convert_string,
            "boolean": self._convert_boolean,
            "char": self._convert_char,
            "binary_expression": self._convert_binary_expression,
            "unary_expression": self._convert_unary_expression,
            "call_expression": self._convert_call,
            "method_call_expression": self._convert_method_call,
            "field_expression": self._convert_field_expression,
            "index_expression": self._convert_index_expression,
            "array_expression": self._convert_array_expression,
            "struct_expression": self._convert_struct_expression,
            "tuple_expression": self._convert_tuple_expression,
            "if_expression": self._convert_if_expression,
            "match_expression": self._convert_match_expression,
            "loop_expression": self._convert_loop_expression,
            "while_expression": self._convert_while_expression,
            "for_expression": self._convert_for_expression,
            "closure_expression": self._convert_closure,
            "path_expression": self._convert_path_expression,
        }

        converter = converters.get(node.type)
        if converter:
            return converter(node, source)

        return self._convert_identifier(node, source)

    def _convert_identifier(self, node: Any, source: str) -> IdentifierNode:
        """Convert an identifier."""
        name = node.text.decode() if hasattr(node, "text") else str(node)
        return IdentifierNode(name=name, language=Language.RUST)

    def _convert_integer(self, node: Any, source: str) -> LiteralNode:
        """Convert an integer literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        return LiteralNode(value=int(value), raw_value=value, literal_type="integer", language=Language.RUST)

    def _convert_float(self, node: Any, source: str) -> LiteralNode:
        """Convert a float literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        return LiteralNode(value=float(value), raw_value=value, literal_type="float", language=Language.RUST)

    def _convert_string(self, node: Any, source: str) -> LiteralNode:
        """Convert a string literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        # Remove quotes
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        return LiteralNode(value=value, raw_value=node.text.decode() if hasattr(node, "text") else str(node), literal_type="string", language=Language.RUST)

    def _convert_boolean(self, node: Any, source: str) -> LiteralNode:
        """Convert a boolean literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        return LiteralNode(value=value == "true", raw_value=value, literal_type="boolean", language=Language.RUST)

    def _convert_char(self, node: Any, source: str) -> LiteralNode:
        """Convert a char literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        return LiteralNode(value=value, raw_value=value, literal_type="char", language=Language.RUST)

    def _convert_binary_expression(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert a binary expression."""
        left: Optional[ASTNode] = None
        right: Optional[ASTNode] = None
        operator = ""

        for child in node.children:
            if child.is_named:
                if not left:
                    left = self._convert_expression(child, source)
                elif not right:
                    right = self._convert_expression(child, source)
            elif child.type in {"+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "&", "|", "^", "<<", ">>", "=", "+=", "-=", "*=", "/="}:
                operator = child.text.decode() if hasattr(child, "text") else str(child)

        if left and right:
            return BinaryOpNode(operator=operator, left=left, right=right, language=Language.RUST)
        return None

    def _convert_unary_expression(self, node: Any, source: str) -> UnaryOpNode:
        """Convert a unary expression."""
        operator = ""
        operand: Optional[ASTNode] = None

        for child in node.children:
            if child.type in {"-", "!", "*", "&", "&mut"}:
                operator = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.is_named:
                operand = self._convert_expression(child, source)

        return UnaryOpNode(
            operator=operator,
            operand=operand or IdentifierNode(name="", language=Language.RUST),
            language=Language.RUST,
        )

    def _convert_call(self, node: Any, source: str) -> CallNode:
        """Convert a call expression."""
        callee: Optional[ASTNode] = None
        arguments: list[ASTNode] = []

        for child in node.children:
            if child.type == "identifier" or child.type == "field_expression":
                callee = self._convert_expression(child, source)
            elif child.type == "arguments":
                for arg in child.children:
                    if arg.is_named:
                        converted = self._convert_expression(arg, source)
                        if converted:
                            arguments.append(converted)

        return CallNode(
            callee=callee or IdentifierNode(name="", language=Language.RUST),
            arguments=arguments,
            language=Language.RUST,
        )

    def _convert_method_call(self, node: Any, source: str) -> CallNode:
        """Convert a method call expression."""
        return self._convert_call(node, source)

    def _convert_field_expression(self, node: Any, source: str) -> MemberAccessNode:
        """Convert a field expression."""
        obj: Optional[ASTNode] = None
        field_name = ""

        for child in node.children:
            if not obj:
                obj = self._convert_expression(child, source)
            elif child.type == "field_identifier":
                field_name = child.text.decode() if hasattr(child, "text") else str(child)

        return MemberAccessNode(
            object=obj or IdentifierNode(name="", language=Language.RUST),
            property_name=field_name,
            language=Language.RUST,
        )

    def _convert_index_expression(self, node: Any, source: str) -> CallNode:
        """Convert an index expression."""
        obj: Optional[ASTNode] = None
        index: Optional[ASTNode] = None

        for child in node.children:
            if not obj:
                obj = self._convert_expression(child, source)
            elif child.is_named:
                index = self._convert_expression(child, source)

        return CallNode(
            callee=obj or IdentifierNode(name="", language=Language.RUST),
            arguments=[index] if index else [],
            language=Language.RUST,
        )

    def _convert_array_expression(self, node: Any, source: str) -> ArrayLiteralNode:
        """Convert an array expression."""
        elements: list[ASTNode] = []
        for child in node.children:
            if child.type in {"integer", "float", "string", "boolean", "identifier", "binary_expression", "call_expression"}:
                converted = self._convert_expression(child, source)
                if converted:
                    elements.append(converted)
        return ArrayLiteralNode(elements=elements, language=Language.RUST)

    def _convert_struct_expression(self, node: Any, source: str) -> ObjectLiteralNode:
        """Convert a struct expression."""
        properties: list[PropertyNode] = []
        for child in node.children:
            if child.type == "field_initializer":
                key: Optional[ASTNode] = None
                value: Optional[ASTNode] = None
                for c in child.children:
                    if not key:
                        key = self._convert_expression(c, source)
                    else:
                        value = self._convert_expression(c, source)
                if key:
                    properties.append(PropertyNode(key=key, value=value, language=Language.RUST))
        return ObjectLiteralNode(properties=properties, language=Language.RUST)

    def _convert_tuple_expression(self, node: Any, source: str) -> ArrayLiteralNode:
        """Convert a tuple expression."""
        elements: list[ASTNode] = []
        for child in node.children:
            if child.is_named:
                converted = self._convert_expression(child, source)
                if converted:
                    elements.append(converted)
        return ArrayLiteralNode(elements=elements, language=Language.RUST)

    def _convert_if_expression(self, node: Any, source: str) -> IfStatementNode:
        """Convert an if expression."""
        condition: Optional[ASTNode] = None
        consequent: Optional[ASTNode] = None
        alternate: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "condition":
                for c in child.children:
                    if c.is_named:
                        condition = self._convert_expression(c, source)
            elif child.type == "block":
                if not consequent:
                    consequent = self._convert_block(child, source)
                else:
                    alternate = self._convert_block(child, source)
            elif child.type == "if_expression":
                alternate = self._convert_if_expression(child, source)

        return IfStatementNode(
            condition=condition or IdentifierNode(name="true", language=Language.RUST),
            consequent=consequent or BlockNode(statements=[], language=Language.RUST),
            alternate=alternate,
            language=Language.RUST,
        )

    def _convert_match_expression(self, node: Any, source: str) -> MatchStatementNode:
        """Convert a match expression."""
        expression: Optional[ASTNode] = None
        cases: list[MatchCaseNode] = []

        for child in node.children:
            if not expression and child.is_named:
                expression = self._convert_expression(child, source)
            elif child.type == "match_arm":
                cases.append(self._convert_match_arm(child, source))

        return MatchStatementNode(
            expression=expression or IdentifierNode(name="", language=Language.RUST),
            cases=cases,
            language=Language.RUST,
        )

    def _convert_match_arm(self, node: Any, source: str) -> MatchCaseNode:
        """Convert a match arm."""
        pattern: Optional[ASTNode] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "pattern":
                pattern = self._convert_pattern(child, source)
            elif child.type == "block":
                body = self._convert_block(child, source)
            elif child.is_named and not pattern:
                pattern = self._convert_expression(child, source)

        return MatchCaseNode(
            pattern=pattern or IdentifierNode(name="_", language=Language.RUST),
            body=body or BlockNode(statements=[], language=Language.RUST),
            language=Language.RUST,
        )

    def _convert_pattern(self, node: Any, source: str) -> IdentifierNode:
        """Convert a pattern."""
        name = node.text.decode() if hasattr(node, "text") else str(node)
        return IdentifierNode(name=name, language=Language.RUST)

    def _convert_loop_expression(self, node: Any, source: str) -> WhileLoopNode:
        """Convert a loop expression."""
        body: Optional[BlockNode] = None
        for child in node.children:
            if child.type == "block":
                body = self._convert_block(child, source)
        return WhileLoopNode(
            condition=IdentifierNode(name="true", language=Language.RUST),
            body=body or BlockNode(statements=[], language=Language.RUST),
            language=Language.RUST,
        )

    def _convert_while_expression(self, node: Any, source: str) -> WhileLoopNode:
        """Convert a while expression."""
        condition: Optional[ASTNode] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "condition":
                for c in child.children:
                    if c.is_named:
                        condition = self._convert_expression(c, source)
            elif child.type == "block":
                body = self._convert_block(child, source)

        return WhileLoopNode(
            condition=condition or IdentifierNode(name="true", language=Language.RUST),
            body=body or BlockNode(statements=[], language=Language.RUST),
            language=Language.RUST,
        )

    def _convert_for_expression(self, node: Any, source: str) -> ForLoopNode:
        """Convert a for expression."""
        initializer: Optional[ASTNode] = None
        condition: Optional[ASTNode] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "identifier":
                initializer = self._convert_identifier(child, source)
            elif child.type == "in":
                continue
            elif child.is_named and not condition:
                condition = self._convert_expression(child, source)
            elif child.type == "block":
                body = self._convert_block(child, source)

        return ForLoopNode(
            initializer=initializer,
            condition=condition,
            body=body or BlockNode(statements=[], language=Language.RUST),
            language=Language.RUST,
        )

    def _convert_closure(self, node: Any, source: str) -> LambdaNode:
        """Convert a closure expression."""
        parameters: list[ParameterNode] = []
        body: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "parameters":
                parameters = self._convert_parameters(child, source)
            elif child.type == "block":
                body = self._convert_block(child, source)
            elif child.is_named:
                body = self._convert_expression(child, source)

        return LambdaNode(
            parameters=parameters,
            body=body or BlockNode(statements=[], language=Language.RUST),
            is_arrow=False,
            language=Language.RUST,
        )

    def _convert_path_expression(self, node: Any, source: str) -> IdentifierNode:
        """Convert a path expression."""
        path_parts = []
        for child in node.children:
            if child.type == "identifier" or child.type == "primitive_type":
                path_parts.append(child.text.decode() if hasattr(child, "text") else str(child))
        return IdentifierNode(name="::".join(path_parts), language=Language.RUST)

    def _convert_type_annotation(self, node: Any, source: str) -> TypeAnnotation:
        """Convert a type annotation."""
        type_name = ""
        for child in node.children:
            if child.type in {"type_identifier", "primitive_type"}:
                type_name = child.text.decode() if hasattr(child, "text") else str(child)
        return TypeAnnotation(type_name=type_name)
