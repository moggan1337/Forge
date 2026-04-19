"""
Go parser using tree-sitter.

Provides AST parsing for Go source code.
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


class GoParser:
    """
    Parser for Go source code.

    Uses tree-sitter for parsing when available.
    """

    def __init__(self) -> None:
        """Initialize the Go parser."""
        self._parser = None
        if TREE_SITTER_AVAILABLE:
            self._parser = get_parser("go")

    @property
    def language(self) -> Language:
        """Get the language this parser handles."""
        return Language.GO

    def parse(self, source_code: str) -> ParseResult:
        """
        Parse Go source code into an AST.

        Args:
            source_code: The Go source code to parse

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
                language=Language.GO,
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[ParseError(message=str(e), line=1, column=0)],
                source_code=source_code,
                language=Language.GO,
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
            if not stripped or stripped.startswith("//"):
                continue

            # Create basic identifier nodes
            if stripped:
                statements.append(
                    IdentifierNode(
                        name=stripped[:50],
                        source_code=stripped,
                        language=Language.GO,
                    )
                )

        program = ProgramNode(
            body=statements,
            language=Language.GO,
            source_code=source_code,
        )

        return ParseResult(
            success=True,
            ast=program,
            errors=errors,
            warnings=warnings,
            source_code=source_code,
            language=Language.GO,
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
                converted = self._convert_declaration(child, source)
                if converted:
                    body.append(converted)
            return ProgramNode(body=body, language=Language.GO, source_code=source)

        return None

    def _convert_declaration(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert a Go declaration."""
        converters = {
            "function_declaration": self._convert_function_decl,
            "method_declaration": self._convert_method_decl,
            "type_declaration": self._convert_type_decl,
            "const_declaration": self._convert_const_decl,
            "var_declaration": self._convert_var_decl,
            "import_declaration": self._convert_import_decl,
        }

        converter = converters.get(node.type)
        if converter:
            return converter(node, source)

        return self._convert_statement(node, source)

    def _convert_function_decl(self, node: Any, source: str) -> FunctionDeclarationNode:
        """Convert a function declaration."""
        name = ""
        parameters: list[ParameterNode] = []
        return_type: Optional[TypeAnnotation] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "parameter_list":
                parameters = self._convert_parameter_list(child, source)
            elif child.type == "result":
                return_type = self._convert_result(child, source)
            elif child.type == "block":
                body = self._convert_block(child, source)

        return FunctionDeclarationNode(
            name=name,
            parameters=parameters,
            body=body,
            return_type=return_type,
            language=Language.GO,
        )

    def _convert_method_decl(self, node: Any, source: str) -> FunctionDeclarationNode:
        """Convert a method declaration."""
        func = self._convert_function_decl(node, source)
        func.name = f"(receiver).{func.name}"
        return func

    def _convert_type_decl(self, node: Any, source: str) -> ClassDeclarationNode:
        """Convert a type declaration."""
        name = ""
        body: list[ASTNode] = []

        for child in node.children:
            if child.type == "type_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "struct_type":
                body = self._convert_struct_type(child, source)
            elif child.type == "interface_type":
                body = self._convert_interface_type(child, source)

        return ClassDeclarationNode(
            name=name,
            body=body,
            language=Language.GO,
        )

    def _convert_struct_type(self, node: Any, source: str) -> list[ASTNode]:
        """Convert a struct type."""
        fields: list[ASTNode] = []
        for child in node.children:
            if child.type == "field_declaration":
                fields.append(self._convert_field_decl(child, source))
        return fields

    def _convert_interface_type(self, node: Any, source: str) -> list[ASTNode]:
        """Convert an interface type."""
        methods: list[ASTNode] = []
        for child in node.children:
            if child.type == "method_specification":
                methods.append(self._convert_method_spec(child, source))
        return methods

    def _convert_field_decl(self, node: Any, source: str) -> VariableDeclarationNode:
        """Convert a field declaration."""
        name = ""
        field_type: Optional[TypeAnnotation] = None

        for child in node.children:
            if child.type == "field_identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type == "type_identifier" or child.type == "pointer_type" or child.type == "slice_type":
                field_type = self._convert_type(child, source)

        return VariableDeclarationNode(
            name=name,
            variable_type=field_type,
            language=Language.GO,
        )

    def _convert_method_spec(self, node: Any, source: str) -> IdentifierNode:
        """Convert a method specification."""
        name = ""
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
        return IdentifierNode(name=name, language=Language.GO)

    def _convert_const_decl(self, node: Any, source: str) -> list[VariableDeclarationNode]:
        """Convert a const declaration."""
        results = []
        for child in node.children:
            if child.type == "const_spec":
                results.extend(self._convert_const_spec(child, source))
        return results

    def _convert_const_spec(self, node: Any, source: str) -> list[VariableDeclarationNode]:
        """Convert a const specification."""
        results: list[VariableDeclarationNode] = []
        names: list[str] = []
        values: list[Optional[ASTNode]] = []

        for child in node.children:
            if child.type == "identifier":
                names.append(child.text.decode() if hasattr(child, "text") else str(child))
            elif child.type in {"integer", "float", "string", "rune", "interpreted_string_literal", "raw_string_literal"}:
                values.append(self._convert_literal(child, source))

        for name in names:
            value = values.pop(0) if values else None
            results.append(
                VariableDeclarationNode(
                    name=name,
                    initializer=value,
                    is_constant=True,
                    language=Language.GO,
                )
            )

        return results

    def _convert_var_decl(self, node: Any, source: str) -> list[VariableDeclarationNode]:
        """Convert a var declaration."""
        results = []
        for child in node.children:
            if child.type == "var_spec":
                results.extend(self._convert_var_spec(child, source))
        return results

    def _convert_var_spec(self, node: Any, source: str) -> list[VariableDeclarationNode]:
        """Convert a var specification."""
        results: list[VariableDeclarationNode] = []
        names: list[str] = []
        var_type: Optional[TypeAnnotation] = None
        values: list[Optional[ASTNode]] = []

        for child in node.children:
            if child.type == "identifier":
                names.append(child.text.decode() if hasattr(child, "text") else str(child))
            elif child.type in {"type_identifier", "pointer_type", "slice_type", "array_type", "map_type", "chan_type"}:
                var_type = self._convert_type(child, source)
            elif child.type in {"integer", "float", "string", "identifier", "binary_expression", "call_expression"}:
                values.append(self._convert_expression(child, source))

        for name in names:
            value = values.pop(0) if values else None
            results.append(
                VariableDeclarationNode(
                    name=name,
                    variable_type=var_type,
                    initializer=value,
                    language=Language.GO,
                )
            )

        return results

    def _convert_import_decl(self, node: Any, source: str) -> list[ImportNode]:
        """Convert an import declaration."""
        imports: list[ImportNode] = []
        for child in node.children:
            if child.type == "import_spec":
                imports.append(self._convert_import_spec(child, source))
        return imports

    def _convert_import_spec(self, node: Any, source: str) -> ImportNode:
        """Convert an import specification."""
        alias = ""
        module_name = ""

        for child in node.children:
            if child.type == "identifier":
                alias = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.type in {"interpreted_string_literal", "raw_string_literal"}:
                module_name = child.text.decode() if hasattr(child, "text") else str(child)
                # Remove quotes
                if module_name.startswith('"') and module_name.endswith('"'):
                    module_name = module_name[1:-1]
                elif module_name.startswith("'") and module_name.endswith("'"):
                    module_name = module_name[1:-1]

        return ImportNode(
            module_name=module_name,
            imported_names=[alias] if alias else [],
            alias=alias if alias else None,
            language=Language.GO,
        )

    def _convert_parameter_list(self, node: Any, source: str) -> list[ParameterNode]:
        """Convert a parameter list."""
        parameters: list[ParameterNode] = []
        for child in node.children:
            if child.type == "parameter_declaration":
                parameters.append(self._convert_parameter_decl(child, source))
        return parameters

    def _convert_parameter_decl(self, node: Any, source: str) -> ParameterNode:
        """Convert a parameter declaration."""
        names: list[str] = []
        param_type: Optional[TypeAnnotation] = None

        for child in node.children:
            if child.type == "identifier":
                names.append(child.text.decode() if hasattr(child, "text") else str(child))
            elif child.type in {"type_identifier", "pointer_type", "slice_type", "array_type", "map_type", "chan_type", "interface_type"}:
                param_type = self._convert_type(child, source)

        return ParameterNode(
            name=", ".join(names) if names else "",
            parameter_type=param_type,
            language=Language.GO,
        )

    def _convert_result(self, node: Any, source: str) -> Optional[TypeAnnotation]:
        """Convert a function result."""
        for child in node.children:
            if child.type in {"type_identifier", "pointer_type", "slice_type", "array_type", "map_type", "chan_type", "interface_type"}:
                return self._convert_type(child, source)
        return None

    def _convert_type(self, node: Any, source: str) -> TypeAnnotation:
        """Convert a type."""
        type_name = ""

        if node.type == "type_identifier":
            type_name = node.text.decode() if hasattr(node, "text") else str(node)
        elif node.type == "pointer_type":
            inner = self._convert_type(node.children[1] if len(node.children) > 1 else node.children[0], source)
            return TypeAnnotation(type_name=f"*{inner.type_name}")
        elif node.type == "slice_type":
            inner = self._convert_type(node.children[1] if len(node.children) > 1 else node.children[0], source)
            return TypeAnnotation(type_name=f"[]{inner.type_name}", is_array=True)
        elif node.type == "array_type":
            return TypeAnnotation(type_name="array", is_array=True)
        elif node.type == "map_type":
            return TypeAnnotation(type_name="map")
        elif node.type == "chan_type":
            return TypeAnnotation(type_name="chan")
        elif node.type == "interface_type":
            return TypeAnnotation(type_name="interface{}")

        return TypeAnnotation(type_name=type_name)

    def _convert_block(self, node: Any, source: str) -> BlockNode:
        """Convert a block."""
        statements: list[ASTNode] = []
        for child in node.children:
            converted = self._convert_statement(child, source)
            if converted:
                statements.append(converted)
        return BlockNode(statements=statements, language=Language.GO)

    def _convert_statement(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert a statement."""
        converters = {
            "return_statement": self._convert_return,
            "if_statement": self._convert_if,
            "for_statement": self._convert_for,
            "switch_statement": self._convert_switch,
            "select_statement": self._convert_select,
            "defer_statement": self._convert_defer,
            "go_statement": self._convert_go,
            "break_statement": self._convert_break,
            "continue_statement": self._convert_continue,
            "goto_statement": self._convert_goto,
            "fallthrough_statement": self._convert_fallthrough,
            "block": self._convert_block,
            "expression_statement": self._convert_expression_statement,
            "inc_statement": self._convert_inc,
            "dec_statement": self._convert_dec,
            "assignment_statement": self._convert_assignment,
            "short_var_declaration": self._convert_short_var_decl,
            "send_statement": self._convert_send,
        }

        converter = converters.get(node.type)
        if converter:
            return converter(node, source)

        return self._convert_expression(node, source)

    def _convert_return(self, node: Any, source: str) -> ReturnStatementNode:
        """Convert a return statement."""
        argument: Optional[ASTNode] = None

        for child in node.children:
            if child.is_named:
                argument = self._convert_expression(child, source)

        return ReturnStatementNode(argument=argument, language=Language.GO)

    def _convert_if(self, node: Any, source: str) -> IfStatementNode:
        """Convert an if statement."""
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
            elif child.type == "if_statement":
                alternate = self._convert_if(child, source)

        return IfStatementNode(
            condition=condition or IdentifierNode(name="true", language=Language.GO),
            consequent=consequent or BlockNode(statements=[], language=Language.GO),
            alternate=alternate,
            language=Language.GO,
        )

    def _convert_for(self, node: Any, source: str) -> ForLoopNode:
        """Convert a for statement."""
        initializer: Optional[ASTNode] = None
        condition: Optional[ASTNode] = None
        update: Optional[ASTNode] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "for_clause":
                for c in child.children:
                    if c.type == "short_var_declaration":
                        initializer = self._convert_short_var_decl(c, source)
                    elif c.type == "assignment_statement":
                        initializer = self._convert_assignment(c, source)
                    elif c.is_named and not condition:
                        condition = self._convert_expression(c, source)
                    elif c.type == "update":
                        update = self._convert_expression(c, source)
            elif child.type == "range_clause":
                pass
            elif child.type == "block":
                body = self._convert_block(child, source)

        return ForLoopNode(
            initializer=initializer,
            condition=condition,
            update=update,
            body=body or BlockNode(statements=[], language=Language.GO),
            language=Language.GO,
        )

    def _convert_switch(self, node: Any, source: str) -> MatchStatementNode:
        """Convert a switch statement."""
        expression: Optional[ASTNode] = None
        cases: list[MatchCaseNode] = []

        for child in node.children:
            if child.type == "expression":
                expression = self._convert_expression(child, source)
            elif child.type == "switch_case":
                cases.append(self._convert_switch_case(child, source))

        return MatchStatementNode(
            expression=expression or IdentifierNode(name="", language=Language.GO),
            cases=cases,
            language=Language.GO,
        )

    def _convert_switch_case(self, node: Any, source: str) -> MatchCaseNode:
        """Convert a switch case."""
        pattern: Optional[ASTNode] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "expression_list":
                for e in child.children:
                    if e.is_named:
                        pattern = self._convert_expression(e, source)
            elif child.type == "block":
                body = self._convert_block(child, source)

        return MatchCaseNode(
            pattern=pattern or IdentifierNode(name="default", language=Language.GO),
            body=body or BlockNode(statements=[], language=Language.GO),
            language=Language.GO,
        )

    def _convert_select(self, node: Any, source: str) -> MatchStatementNode:
        """Convert a select statement."""
        return self._convert_switch(node, source)

    def _convert_defer(self, node: Any, source: str) -> IdentifierNode:
        """Convert a defer statement."""
        return IdentifierNode(name="defer", language=Language.GO)

    def _convert_go(self, node: Any, source: str) -> IdentifierNode:
        """Convert a go statement."""
        return IdentifierNode(name="go", language=Language.GO)

    def _convert_break(self, node: Any, source: str) -> IdentifierNode:
        """Convert a break statement."""
        return IdentifierNode(name="break", language=Language.GO)

    def _convert_continue(self, node: Any, source: str) -> IdentifierNode:
        """Convert a continue statement."""
        return IdentifierNode(name="continue", language=Language.GO)

    def _convert_goto(self, node: Any, source: str) -> IdentifierNode:
        """Convert a goto statement."""
        return IdentifierNode(name="goto", language=Language.GO)

    def _convert_fallthrough(self, node: Any, source: str) -> IdentifierNode:
        """Convert a fallthrough statement."""
        return IdentifierNode(name="fallthrough", language=Language.GO)

    def _convert_expression_statement(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert an expression statement."""
        for child in node.children:
            if child.is_named:
                return self._convert_expression(child, source)
        return None

    def _convert_inc(self, node: Any, source: str) -> UnaryOpNode:
        """Convert an increment statement."""
        return UnaryOpNode(
            operator="++",
            operand=IdentifierNode(name="", language=Language.GO),
            is_postfix=True,
            language=Language.GO,
        )

    def _convert_dec(self, node: Any, source: str) -> UnaryOpNode:
        """Convert a decrement statement."""
        return UnaryOpNode(
            operator="--",
            operand=IdentifierNode(name="", language=Language.GO),
            is_postfix=True,
            language=Language.GO,
        )

    def _convert_assignment(self, node: Any, source: str) -> BinaryOpNode:
        """Convert an assignment statement."""
        left: Optional[ASTNode] = None
        right: Optional[ASTNode] = None
        operator = "="

        for child in node.children:
            if child.type in {"+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>=", "&^=", "="}:
                operator = child.text.decode() if hasattr(child, "text") else "="
            elif child.is_named:
                if not left:
                    left = self._convert_expression(child, source)
                else:
                    right = self._convert_expression(child, source)

        return BinaryOpNode(
            operator=operator,
            left=left or IdentifierNode(name="", language=Language.GO),
            right=right or IdentifierNode(name="", language=Language.GO),
            language=Language.GO,
        )

    def _convert_short_var_decl(self, node: Any, source: str) -> VariableDeclarationNode:
        """Convert a short variable declaration."""
        name = ""
        value: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.is_named:
                value = self._convert_expression(child, source)

        return VariableDeclarationNode(
            name=name,
            initializer=value,
            language=Language.GO,
        )

    def _convert_send(self, node: Any, source: str) -> IdentifierNode:
        """Convert a send statement."""
        return IdentifierNode(name="send", language=Language.GO)

    def _convert_expression(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert an expression."""
        converters = {
            "identifier": self._convert_identifier,
            "integer": self._convert_integer,
            "float": self._convert_float,
            "string": self._convert_string,
            "rune": self._convert_rune,
            "true": self._convert_true,
            "false": self._convert_false,
            "nil": self._convert_nil,
            "binary_expression": self._convert_binary_expression,
            "unary_expression": self._convert_unary_expression,
            "call_expression": self._convert_call,
            "selector_expression": self._convert_selector,
            "index_expression": self._convert_index,
            "slice_expression": self._convert_slice,
            "type_conversion": self._convert_type_conversion,
            "append": self._convert_append,
            "make": self._convert_make,
            "new": self._convert_new,
            "array_composite_literal": self._convert_array_literal,
            "slice_composite_literal": self._convert_slice_literal,
            "map_composite_literal": self._convert_map_literal,
            "struct_composite_literal": self._convert_struct_literal,
            "function_literal": self._convert_function_literal,
            "go_raw_string_literal": self._convert_string,
            "interpreted_string_literal": self._convert_string,
            "raw_string_literal": self._convert_string,
        }

        converter = converters.get(node.type)
        if converter:
            return converter(node, source)

        return self._convert_identifier(node, source)

    def _convert_identifier(self, node: Any, source: str) -> IdentifierNode:
        """Convert an identifier."""
        name = node.text.decode() if hasattr(node, "text") else str(node)
        return IdentifierNode(name=name, language=Language.GO)

    def _convert_integer(self, node: Any, source: str) -> LiteralNode:
        """Convert an integer literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        return LiteralNode(value=int(value), raw_value=value, literal_type="integer", language=Language.GO)

    def _convert_float(self, node: Any, source: str) -> LiteralNode:
        """Convert a float literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        return LiteralNode(value=float(value), raw_value=value, literal_type="float", language=Language.GO)

    def _convert_string(self, node: Any, source: str) -> LiteralNode:
        """Convert a string literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        # Remove quotes
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        return LiteralNode(value=value, raw_value=node.text.decode() if hasattr(node, "text") else str(node), literal_type="string", language=Language.GO)

    def _convert_rune(self, node: Any, source: str) -> LiteralNode:
        """Convert a rune literal."""
        value = node.text.decode() if hasattr(node, "text") else str(node)
        return LiteralNode(value=value, raw_value=value, literal_type="rune", language=Language.GO)

    def _convert_true(self, node: Any, source: str) -> LiteralNode:
        """Convert a true literal."""
        return LiteralNode(value=True, raw_value="true", literal_type="boolean", language=Language.GO)

    def _convert_false(self, node: Any, source: str) -> LiteralNode:
        """Convert a false literal."""
        return LiteralNode(value=False, raw_value="false", literal_type="boolean", language=Language.GO)

    def _convert_nil(self, node: Any, source: str) -> LiteralNode:
        """Convert a nil literal."""
        return LiteralNode(value=None, raw_value="nil", literal_type="nil", language=Language.GO)

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
            elif child.type in {"+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "&", "|", "^", "<<", ">>", "&^"}:
                operator = child.text.decode() if hasattr(child, "text") else str(child)

        if left and right:
            return BinaryOpNode(operator=operator, left=left, right=right, language=Language.GO)
        return None

    def _convert_unary_expression(self, node: Any, source: str) -> UnaryOpNode:
        """Convert a unary expression."""
        operator = ""
        operand: Optional[ASTNode] = None

        for child in node.children:
            if child.type in {"-", "!", "+", "^", "*", "&"}:
                operator = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.is_named:
                operand = self._convert_expression(child, source)

        return UnaryOpNode(
            operator=operator,
            operand=operand or IdentifierNode(name="", language=Language.GO),
            language=Language.GO,
        )

    def _convert_call(self, node: Any, source: str) -> CallNode:
        """Convert a call expression."""
        callee: Optional[ASTNode] = None
        arguments: list[ASTNode] = []

        for child in node.children:
            if child.is_named:
                callee = self._convert_expression(child, source)
            elif child.type == "argument_list":
                for arg in child.children:
                    if arg.is_named:
                        converted = self._convert_expression(arg, source)
                        if converted:
                            arguments.append(converted)

        return CallNode(
            callee=callee or IdentifierNode(name="", language=Language.GO),
            arguments=arguments,
            language=Language.GO,
        )

    def _convert_selector(self, node: Any, source: str) -> MemberAccessNode:
        """Convert a selector expression."""
        obj: Optional[ASTNode] = None
        field = ""

        for child in node.children:
            if not obj:
                obj = self._convert_expression(child, source)
            elif child.type == "field_identifier":
                field = child.text.decode() if hasattr(child, "text") else str(child)

        return MemberAccessNode(
            object=obj or IdentifierNode(name="", language=Language.GO),
            property_name=field,
            language=Language.GO,
        )

    def _convert_index(self, node: Any, source: str) -> CallNode:
        """Convert an index expression."""
        obj: Optional[ASTNode] = None
        index: Optional[ASTNode] = None

        for child in node.children:
            if not obj:
                obj = self._convert_expression(child, source)
            elif child.is_named:
                index = self._convert_expression(child, source)

        return CallNode(
            callee=obj or IdentifierNode(name="", language=Language.GO),
            arguments=[index] if index else [],
            language=Language.GO,
        )

    def _convert_slice(self, node: Any, source: str) -> CallNode:
        """Convert a slice expression."""
        obj: Optional[ASTNode] = None

        for child in node.children:
            if not obj:
                obj = self._convert_expression(child, source)

        return CallNode(
            callee=obj or IdentifierNode(name="slice", language=Language.GO),
            arguments=[],
            language=Language.GO,
        )

    def _convert_type_conversion(self, node: Any, source: str) -> CallNode:
        """Convert a type conversion."""
        type_name = ""
        value: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "type_identifier":
                type_name = child.text.decode() if hasattr(child, "text") else str(child)
            elif child.is_named:
                value = self._convert_expression(child, source)

        return CallNode(
            callee=IdentifierNode(name=type_name, language=Language.GO),
            arguments=[value] if value else [],
            language=Language.GO,
        )

    def _convert_append(self, node: Any, source: str) -> CallNode:
        """Convert an append call."""
        return CallNode(
            callee=IdentifierNode(name="append", language=Language.GO),
            arguments=[],
            language=Language.GO,
        )

    def _convert_make(self, node: Any, source: str) -> CallNode:
        """Convert a make call."""
        return CallNode(
            callee=IdentifierNode(name="make", language=Language.GO),
            arguments=[],
            language=Language.GO,
        )

    def _convert_new(self, node: Any, source: str) -> CallNode:
        """Convert a new call."""
        return CallNode(
            callee=IdentifierNode(name="new", language=Language.GO),
            arguments=[],
            language=Language.GO,
        )

    def _convert_array_literal(self, node: Any, source: str) -> ArrayLiteralNode:
        """Convert an array literal."""
        return self._convert_literal_array(node, source)

    def _convert_slice_literal(self, node: Any, source: str) -> ArrayLiteralNode:
        """Convert a slice literal."""
        return self._convert_literal_array(node, source)

    def _convert_literal_array(self, node: Any, source: str) -> ArrayLiteralNode:
        """Convert a literal array/slice."""
        elements: list[ASTNode] = []
        for child in node.children:
            if child.is_named:
                converted = self._convert_expression(child, source)
                if converted:
                    elements.append(converted)
        return ArrayLiteralNode(elements=elements, language=Language.GO)

    def _convert_map_literal(self, node: Any, source: str) -> ObjectLiteralNode:
        """Convert a map literal."""
        properties: list[PropertyNode] = []
        for child in node.children:
            if child.type == "element":
                key: Optional[ASTNode] = None
                value: Optional[ASTNode] = None
                for c in child.children:
                    if not key:
                        key = self._convert_expression(c, source)
                    else:
                        value = self._convert_expression(c, source)
                if key:
                    properties.append(PropertyNode(key=key, value=value, language=Language.GO))
        return ObjectLiteralNode(properties=properties, language=Language.GO)

    def _convert_struct_literal(self, node: Any, source: str) -> ObjectLiteralNode:
        """Convert a struct literal."""
        properties: list[PropertyNode] = []
        for child in node.children:
            if child.type == "field_identifier":
                properties.append(PropertyNode(key=self._convert_identifier(child, source), language=Language.GO))
        return ObjectLiteralNode(properties=properties, language=Language.GO)

    def _convert_function_literal(self, node: Any, source: str) -> LambdaNode:
        """Convert a function literal."""
        parameters: list[ParameterNode] = []
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "parameter_list":
                parameters = self._convert_parameter_list(child, source)
            elif child.type == "result":
                pass
            elif child.type == "block":
                body = self._convert_block(child, source)

        return LambdaNode(
            parameters=parameters,
            body=body or BlockNode(statements=[], language=Language.GO),
            is_arrow=False,
            language=Language.GO,
        )

    def _convert_literal(self, node: Any, source: str) -> Optional[ASTNode]:
        """Convert a literal."""
        literal_converters = {
            "integer": self._convert_integer,
            "float": self._convert_float,
            "interpreted_string_literal": self._convert_string,
            "raw_string_literal": self._convert_string,
            "rune": self._convert_rune,
            "true": self._convert_true,
            "false": self._convert_false,
            "nil": self._convert_nil,
        }

        converter = literal_converters.get(node.type)
        if converter:
            return converter(node, source)

        return self._convert_identifier(node, source)
