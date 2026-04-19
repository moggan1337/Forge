"""
TypeScript/JavaScript parser using tree-sitter.

Provides AST parsing for TypeScript and JavaScript source code.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    from tree_sitter_languages import get_language, get_parser
    from tree_sitter import Node as TSSNode, Tree as TSTree

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
    CommentNode,
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
    SourceLocation,
    SourceRange,
    TryStatementNode,
    TypeAnnotation,
    UnaryOpNode,
    VariableDeclarationNode,
    WhileLoopNode,
)
from forge.transpiler.language import Language


class TypeScriptParser:
    """
    Parser for TypeScript and JavaScript source code.

    Uses tree-sitter for robust, error-tolerant parsing.
    """

    def __init__(self) -> None:
        """Initialize the TypeScript parser."""
        self._language = None
        self._parser = None
        if TREE_SITTER_AVAILABLE:
            self._language = get_language("typescript")
            self._parser = get_parser("typescript")

    @property
    def language(self) -> Language:
        """Get the language this parser handles."""
        return Language.TYPESCRIPT

    def parse(self, source_code: str) -> ParseResult:
        """
        Parse TypeScript source code into an AST.

        Args:
            source_code: The TypeScript source code to parse

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
                language=Language.TYPESCRIPT,
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[ParseError(message=str(e), line=1, column=0)],
                source_code=source_code,
                language=Language.TYPESCRIPT,
            )

    def _parse_fallback(self, source_code: str) -> ParseResult:
        """Fallback parser for when tree-sitter is not available."""
        # Simple regex-based parsing for basic constructs
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = [
            ParseWarning(
                message="Using fallback parser - tree-sitter not available. Results may be incomplete.",
                line=1,
                column=0,
            )
        ]

        statements: list[ASTNode] = []

        # Try to identify basic constructs
        lines = source_code.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            # Create a simple identifier node for each line
            if stripped:
                statements.append(
                    IdentifierNode(
                        name=stripped[:50],
                        source_code=stripped,
                        language=Language.TYPESCRIPT,
                    )
                )

        program = ProgramNode(
            body=statements,
            language=Language.TYPESCRIPT,
            source_code=source_code,
        )

        return ParseResult(
            success=True,
            ast=program,
            errors=errors,
            warnings=warnings,
            source_code=source_code,
            language=Language.TYPESCRIPT,
        )

    def _collect_errors(
        self,
        node: TSSNode,
        source: str,
        errors: list[ParseError],
        warnings: list[ParseWarning],
    ) -> None:
        """Recursively collect parse errors from the tree."""
        if node.type == "ERROR":
            start = node.start_point
            errors.append(
                ParseError(
                    message=f"Parse error: {node.text.decode()[:50]}",
                    line=start[0] + 1,
                    column=start[1],
                )
            )
        for child in node.children:
            self._collect_errors(child, source, errors, warnings)

    def _convert_node(self, node: TSSNode, source: str) -> Optional[ProgramNode]:
        """Convert a tree-sitter node to our AST format."""
        if node.type == "program":
            body = []
            for child in node.children:
                converted = self._convert_statement(child, source)
                if converted:
                    body.append(converted)
            return ProgramNode(body=body, language=Language.TYPESCRIPT, source_code=source)

        return None

    def _convert_statement(self, node: TSSNode, source: str) -> Optional[ASTNode]:
        """Convert a statement node."""
        converters = {
            "function_declaration": self._convert_function,
            "class_declaration": self._convert_class,
            "variable_declaration": self._convert_variable,
            "if_statement": self._convert_if,
            "for_statement": self._convert_for,
            "while_statement": self._convert_while,
            "return_statement": self._convert_return,
            "expression_statement": self._convert_expression_statement,
            "import_statement": self._convert_import,
            "export_statement": self._convert_export,
            "try_statement": self._convert_try,
            "switch_statement": self._convert_switch,
            "block": self._convert_block,
        }

        converter = converters.get(node.type)
        if converter:
            return converter(node, source)
        return self._convert_generic(node, source)

    def _convert_expression_statement(self, node: TSSNode, source: str) -> Optional[ASTNode]:
        """Convert an expression statement."""
        if node.children:
            return self._convert_expression(node.children[0], source)
        return None

    def _convert_function(self, node: TSSNode, source: str) -> FunctionDeclarationNode:
        """Convert a function declaration."""
        name = "anonymous"
        parameters: list[ParameterNode] = []
        body: Optional[BlockNode] = None
        return_type: Optional[TypeAnnotation] = None

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode(source.encode() if hasattr(source, 'encode') else source)
            elif child.type == "required_parameter":
                parameters.append(self._convert_parameter(child, source))
            elif child.type == "block":
                body = self._convert_block(child, source)

        return FunctionDeclarationNode(
            name=name,
            parameters=parameters,
            body=body,
            return_type=return_type,
            language=Language.TYPESCRIPT,
        )

    def _convert_class(self, node: TSSNode, source: str) -> ClassDeclarationNode:
        """Convert a class declaration."""
        name = "AnonymousClass"
        base_classes: list[str] = []
        body: list[ASTNode] = []

        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode()
            elif child.type == "extends_clause":
                base_classes.append(child.text.decode())
            elif child.type == "class_body":
                for member in child.children:
                    if member.type == "method_definition":
                        body.append(self._convert_method(member, source))

        return ClassDeclarationNode(
            name=name,
            base_classes=base_classes,
            body=body,
            language=Language.TYPESCRIPT,
        )

    def _convert_method(self, node: TSSNode, source: str) -> FunctionDeclarationNode:
        """Convert a method definition."""
        name = "method"
        parameters: list[ParameterNode] = []
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "property_identifier":
                name = child.text.decode()
            elif child.type == "required_parameter":
                parameters.append(self._convert_parameter(child, source))
            elif child.type == "block":
                body = self._convert_block(child, source)

        return FunctionDeclarationNode(
            name=name,
            parameters=parameters,
            body=body,
            language=Language.TYPESCRIPT,
        )

    def _convert_variable(self, node: TSSNode, source: str) -> VariableDeclarationNode:
        """Convert a variable declaration."""
        name = ""
        initializer: Optional[ASTNode] = None
        is_const = False

        for child in node.children:
            if child.type == "const":
                is_const = True
            elif child.type == "identifier":
                name = child.text.decode()
            elif child.type in {"string", "number", "identifier"}:
                initializer = self._convert_expression(child, source)

        return VariableDeclarationNode(
            name=name,
            initializer=initializer,
            is_constant=is_const,
            language=Language.TYPESCRIPT,
        )

    def _convert_if(self, node: TSSNode, source: str) -> IfStatementNode:
        """Convert an if statement."""
        condition: Optional[ASTNode] = None
        consequent: Optional[ASTNode] = None
        alternate: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "condition":
                for c in child.children:
                    if c.is_named:
                        condition = self._convert_expression(c, source)
            elif child.type == "consequence":
                consequent = self._convert_block(child, source) if child.type == "block" else self._convert_statement(child, source)
            elif child.type == "alternative":
                alternate = self._convert_block(child, source) if child.type == "block" else self._convert_statement(child, source)

        return IfStatementNode(
            condition=condition or IdentifierNode(name="true", language=Language.TYPESCRIPT),
            consequent=consequent or BlockNode(statements=[], language=Language.TYPESCRIPT),
            alternate=alternate,
            language=Language.TYPESCRIPT,
        )

    def _convert_for(self, node: TSSNode, source: str) -> ForLoopNode:
        """Convert a for loop."""
        initializer: Optional[ASTNode] = None
        condition: Optional[ASTNode] = None
        update: Optional[ASTNode] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "for_initializer":
                if child.children:
                    initializer = self._convert_statement(child.children[0], source)
            elif child.type == "for_condition":
                condition = self._convert_expression(child, source)
            elif child.type == "for_update":
                update = self._convert_expression(child, source)
            elif child.type == "block":
                body = self._convert_block(child, source)

        return ForLoopNode(
            initializer=initializer,
            condition=condition,
            update=update,
            body=body or BlockNode(statements=[], language=Language.TYPESCRIPT),
            language=Language.TYPESCRIPT,
        )

    def _convert_while(self, node: TSSNode, source: str) -> WhileLoopNode:
        """Convert a while loop."""
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
            condition=condition or IdentifierNode(name="true", language=Language.TYPESCRIPT),
            body=body or BlockNode(statements=[], language=Language.TYPESCRIPT),
            language=Language.TYPESCRIPT,
        )

    def _convert_return(self, node: TSSNode, source: str) -> ReturnStatementNode:
        """Convert a return statement."""
        argument: Optional[ASTNode] = None

        for child in node.children:
            if child.is_named:
                argument = self._convert_expression(child, source)

        return ReturnStatementNode(argument=argument, language=Language.TYPESCRIPT)

    def _convert_try(self, node: TSSNode, source: str) -> TryStatementNode:
        """Convert a try statement."""
        block: Optional[ASTNode] = None
        handler: Optional[CatchClauseNode] = None
        finalizer: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "block":
                block = self._convert_block(child, source)
            elif child.type == "catch_clause":
                handler = self._convert_catch(child, source)
            elif child.type == "finally_clause":
                for c in child.children:
                    if c.type == "block":
                        finalizer = self._convert_block(c, source)

        return TryStatementNode(
            block=block or BlockNode(statements=[], language=Language.TYPESCRIPT),
            handler=handler,
            finalizer=finalizer,
            language=Language.TYPESCRIPT,
        )

    def _convert_catch(self, node: TSSNode, source: str) -> CatchClauseNode:
        """Convert a catch clause."""
        parameter: Optional[str] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "identifier":
                parameter = child.text.decode()
            elif child.type == "block":
                body = self._convert_block(child, source)

        return CatchClauseNode(
            parameter=parameter,
            body=body or BlockNode(statements=[], language=Language.TYPESCRIPT),
            language=Language.TYPESCRIPT,
        )

    def _convert_switch(self, node: TSSNode, source: str) -> MatchStatementNode:
        """Convert a switch statement to match."""
        expression: Optional[ASTNode] = None
        cases: list[MatchCaseNode] = []

        for child in node.children:
            if child.type == "expression":
                expression = self._convert_expression(child, source)
            elif child.type == "switch_case":
                cases.append(self._convert_case(child, source))

        return MatchStatementNode(
            expression=expression or IdentifierNode(name="", language=Language.TYPESCRIPT),
            cases=cases,
            language=Language.TYPESCRIPT,
        )

    def _convert_case(self, node: TSSNode, source: str) -> MatchCaseNode:
        """Convert a switch case."""
        pattern: Optional[ASTNode] = None
        body: Optional[BlockNode] = None

        for child in node.children:
            if child.type == "switch_pattern":
                pattern = self._convert_expression(child, source)
            elif child.type == "consequence":
                body = self._convert_block(child, source)

        return MatchCaseNode(
            pattern=pattern or IdentifierNode(name="default", language=Language.TYPESCRIPT),
            body=body or BlockNode(statements=[], language=Language.TYPESCRIPT),
            language=Language.TYPESCRIPT,
        )

    def _convert_import(self, node: TSSNode, source: str) -> ImportNode:
        """Convert an import statement."""
        module_name = ""
        imported_names: list[str] = []
        is_default = False
        is_namespace = False

        for child in node.children:
            if child.type == "string":
                module_name = child.text.decode().strip("'\"")
            elif child.type == "identifier":
                imported_names.append(child.text.decode())
                is_default = True
            elif child.type == "asterisk":
                is_namespace = True

        return ImportNode(
            module_name=module_name,
            imported_names=imported_names,
            is_default=is_default,
            is_namespace=is_namespace,
            language=Language.TYPESCRIPT,
        )

    def _convert_export(self, node: TSSNode, source: str) -> ExportNode:
        """Convert an export statement."""
        exported_name = ""
        is_default = False

        for child in node.children:
            if child.type == "default":
                is_default = True
            elif child.type == "identifier":
                exported_name = child.text.decode()

        return ExportNode(
            exported_name=exported_name,
            is_default=is_default,
            language=Language.TYPESCRIPT,
        )

    def _convert_block(self, node: TSSNode, source: str) -> BlockNode:
        """Convert a block."""
        statements: list[ASTNode] = []
        for child in node.children:
            converted = self._convert_statement(child, source)
            if converted:
                statements.append(converted)
        return BlockNode(statements=statements, language=Language.TYPESCRIPT)

    def _convert_expression(self, node: TSSNode, source: str) -> Optional[ASTNode]:
        """Convert an expression node."""
        if node.type in {"identifier", "property_identifier"}:
            return IdentifierNode(name=node.text.decode(), language=Language.TYPESCRIPT)
        elif node.type in {"string", "template_string"}:
            return LiteralNode(
                value=node.text.decode().strip("'\""),
                raw_value=node.text.decode(),
                literal_type="string",
                language=Language.TYPESCRIPT,
            )
        elif node.type in {"number", "integer"}:
            try:
                value = int(node.text.decode())
            except ValueError:
                value = float(node.text.decode())
            return LiteralNode(value=value, raw_value=node.text.decode(), literal_type="number", language=Language.TYPESCRIPT)
        elif node.type in {"true", "false"}:
            return LiteralNode(value=node.text.decode() == "true", raw_value=node.text.decode(), literal_type="boolean", language=Language.TYPESCRIPT)
        elif node.type == "binary_expression":
            return self._convert_binary_expression(node, source)
        elif node.type == "call_expression":
            return self._convert_call(node, source)
        elif node.type == "member_expression":
            return self._convert_member_access(node, source)
        elif node.type == "array":
            return self._convert_array(node, source)
        elif node.type == "object":
            return self._convert_object(node, source)
        elif node.type == "arrow_function":
            return self._convert_arrow_function(node, source)
        return self._convert_generic(node, source)

    def _convert_binary_expression(self, node: TSSNode, source: str) -> Optional[ASTNode]:
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
            elif child.type in {"+", "-", "*", "/", "%", "==", "===", "!=", "!==", "<", ">", "<=", ">=", "&&", "||", "=", "+=", "-=", "*=", "/="}:
                operator = child.text.decode()

        if left and right:
            return BinaryOpNode(operator=operator, left=left, right=right, language=Language.TYPESCRIPT)
        return None

    def _convert_call(self, node: TSSNode, source: str) -> CallNode:
        """Convert a call expression."""
        callee: Optional[ASTNode] = None
        arguments: list[ASTNode] = []

        for child in node.children:
            if child.type == "identifier" or child.type == "member_expression":
                callee = self._convert_expression(child, source)
            elif child.type == "arguments":
                for arg in child.children:
                    if arg.is_named:
                        converted = self._convert_expression(arg, source)
                        if converted:
                            arguments.append(converted)

        return CallNode(
            callee=callee or IdentifierNode(name="unknown", language=Language.TYPESCRIPT),
            arguments=arguments,
            language=Language.TYPESCRIPT,
        )

    def _convert_member_access(self, node: TSSNode, source: str) -> MemberAccessNode:
        """Convert a member expression."""
        obj: Optional[ASTNode] = None
        property_name = ""
        is_safe = False

        for child in node.children:
            if child.type == "optional_chain":
                is_safe = True
            elif not obj:
                obj = self._convert_expression(child, source)
            else:
                if child.type == "property_identifier":
                    property_name = child.text.decode()

        return MemberAccessNode(
            object=obj or IdentifierNode(name="", language=Language.TYPESCRIPT),
            property_name=property_name,
            is_safe=is_safe,
            language=Language.TYPESCRIPT,
        )

    def _convert_array(self, node: TSSNode, source: str) -> ArrayLiteralNode:
        """Convert an array literal."""
        elements: list[ASTNode] = []
        for child in node.children:
            if child.is_named:
                converted = self._convert_expression(child, source)
                if converted:
                    elements.append(converted)
        return ArrayLiteralNode(elements=elements, language=Language.TYPESCRIPT)

    def _convert_object(self, node: TSSNode, source: str) -> ObjectLiteralNode:
        """Convert an object literal."""
        properties: list[PropertyNode] = []
        for child in node.children:
            if child.type == "pair":
                key: Optional[ASTNode] = None
                value: Optional[ASTNode] = None
                for c in child.children:
                    if not key:
                        key = self._convert_expression(c, source)
                    else:
                        value = self._convert_expression(c, source)
                if key:
                    properties.append(PropertyNode(key=key, value=value, language=Language.TYPESCRIPT))
        return ObjectLiteralNode(properties=properties, language=Language.TYPESCRIPT)

    def _convert_arrow_function(self, node: TSSNode, source: str) -> LambdaNode:
        """Convert an arrow function."""
        parameters: list[ParameterNode] = []
        body: Optional[ASTNode] = None

        for child in node.children:
            if child.type == "required_parameter":
                parameters.append(self._convert_parameter(child, source))
            elif child.type == "block":
                body = self._convert_block(child, source)
            elif child.type == "expression_statement":
                for c in child.children:
                    if c.is_named:
                        body = self._convert_expression(c, source)

        return LambdaNode(
            parameters=parameters,
            body=body or BlockNode(statements=[], language=Language.TYPESCRIPT),
            is_arrow=True,
            language=Language.TYPESCRIPT,
        )

    def _convert_parameter(self, node: TSSNode, source: str) -> ParameterNode:
        """Convert a parameter."""
        name = ""
        for child in node.children:
            if child.type == "identifier":
                name = child.text.decode()
        return ParameterNode(name=name, language=Language.TYPESCRIPT)

    def _convert_generic(self, node: TSSNode, source: str) -> IdentifierNode:
        """Convert any node to a generic identifier."""
        return IdentifierNode(name=node.text.decode()[:100], source_code=node.text.decode(), language=Language.TYPESCRIPT)
