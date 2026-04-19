"""
Python parser using the built-in ast module.

Provides AST parsing for Python source code.
"""

from __future__ import annotations

import ast
from typing import Any, Optional

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
    TryStatementNode,
    TypeAnnotation,
    UnaryOpNode,
    VariableDeclarationNode,
    WhileLoopNode,
)
from forge.transpiler.language import Language


class PythonParser:
    """
    Parser for Python source code.

    Uses Python's built-in ast module for parsing.
    """

    def __init__(self) -> None:
        """Initialize the Python parser."""
        pass

    @property
    def language(self) -> Language:
        """Get the language this parser handles."""
        return Language.PYTHON

    def parse(self, source_code: str) -> ParseResult:
        """
        Parse Python source code into an AST.

        Args:
            source_code: The Python source code to parse

        Returns:
            ParseResult containing the AST and any errors/warnings
        """
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []

        try:
            tree = ast.parse(source_code)

            # Convert to our AST format
            ast_node = self._convert_module(tree, source_code)
            if ast_node:
                ast_node.source_code = source_code

            return ParseResult(
                success=True,
                ast=ast_node,
                errors=errors,
                warnings=warnings,
                source_code=source_code,
                language=Language.PYTHON,
            )
        except SyntaxError as e:
            errors.append(
                ParseError(
                    message=str(e),
                    line=e.lineno or 1,
                    column=e.offset or 0,
                )
            )
            return ParseResult(
                success=False,
                errors=errors,
                source_code=source_code,
                language=Language.PYTHON,
            )
        except Exception as e:
            errors.append(ParseError(message=str(e), line=1, column=0))
            return ParseResult(
                success=False,
                errors=errors,
                source_code=source_code,
                language=Language.PYTHON,
            )

    def _convert_module(self, node: ast.Module, source: str) -> ProgramNode:
        """Convert an ast.Module to our ProgramNode."""
        statements: list[ASTNode] = []
        for stmt in node.body:
            converted = self._convert_statement(stmt, source)
            if converted:
                statements.append(converted)
        return ProgramNode(body=statements, language=Language.PYTHON, source_code=source)

    def _convert_statement(self, node: ast.stmt, source: str) -> Optional[ASTNode]:
        """Convert a Python statement to our AST format."""
        converters = {
            ast.FunctionDef: self._convert_function,
            ast.AsyncFunctionDef: self._convert_async_function,
            ast.ClassDef: self._convert_class,
            ast.Assign: self._convert_assign,
            ast.AnnAssign: self._convert_annotated_assign,
            ast.Return: self._convert_return,
            ast.If: self._convert_if,
            ast.For: self._convert_for,
            ast.AsyncFor: self._convert_async_for,
            ast.While: self._convert_while,
            ast.Break: self._convert_break,
            ast.Continue: self._convert_continue,
            ast.Pass: self._convert_pass,
            ast.Raise: self._convert_raise,
            ast.Try: self._convert_try,
            ast.With: self._convert_with,
            ast.AsyncWith: self._convert_async_with,
            ast.Expr: self._convert_expr,
            ast.Import: self._convert_import,
            ast.ImportFrom: self._convert_import_from,
            ast.Global: self._convert_global,
            ast.Nonlocal: self._convert_nonlocal,
            ast.Assert: self._convert_assert,
            ast.Match: self._convert_match,
            ast.Delete: self._convert_delete,
        }

        for node_type, converter in converters.items():
            if isinstance(node, node_type):
                return converter(node, source)

        return None

    def _convert_expression(self, node: ast.expr, source: str) -> Optional[ASTNode]:
        """Convert a Python expression to our AST format."""
        converters = {
            ast.Name: self._convert_name,
            ast.Constant: self._convert_constant,
            ast.BinOp: self._convert_binop,
            ast.UnaryOp: self._convert_unaryop,
            ast.BoolOp: self._convert_boolop,
            ast.Compare: self._convert_compare,
            ast.Call: self._convert_call,
            ast.Attribute: self._convert_attribute,
            ast.Subscript: self._convert_subscript,
            ast.List: self._convert_list,
            ast.Tuple: self._convert_tuple,
            ast.Dict: self._convert_dict,
            ast.Set: self._convert_set,
            ast.Lambda: self._convert_lambda,
            ast.IfExp: self._convert_ifexp,
            ast.JoinedStr: self._convert_fstring,
            ast.Slice: self._convert_slice,
            ast.Starred: self._convert_starred,
            ast.Yield: self._convert_yield,
            ast.YieldFrom: self._convert_yieldfrom,
            ast.Await: self._convert_await,
            ast.FormattedValue: self._convert_formatted_value,
        }

        for node_type, converter in converters.items():
            if isinstance(node, node_type):
                return converter(node, source)

        return None

    def _convert_function(self, node: ast.FunctionDef, source: str) -> FunctionDeclarationNode:
        """Convert a function definition."""
        name = node.name
        parameters = self._convert_args(node.args, source)
        body = self._convert_body(node.body, source)
        return_type = self._get_annotation(node.returns)

        return FunctionDeclarationNode(
            name=name,
            parameters=parameters,
            body=body,
            return_type=return_type,
            is_async=False,
            language=Language.PYTHON,
        )

    def _convert_async_function(self, node: ast.AsyncFunctionDef, source: str) -> FunctionDeclarationNode:
        """Convert an async function definition."""
        name = node.name
        parameters = self._convert_args(node.args, source)
        body = self._convert_body(node.body, source)
        return_type = self._get_annotation(node.returns)

        return FunctionDeclarationNode(
            name=name,
            parameters=parameters,
            body=body,
            return_type=return_type,
            is_async=True,
            language=Language.PYTHON,
        )

    def _convert_class(self, node: ast.ClassDef, source: str) -> ClassDeclarationNode:
        """Convert a class definition."""
        name = node.name
        base_classes = [self._get_name_str(base) for base in node.bases]
        body = self._convert_body(node.body, source)

        return ClassDeclarationNode(
            name=name,
            base_classes=base_classes,
            body=body,
            language=Language.PYTHON,
        )

    def _convert_assign(self, node: ast.Assign, source: str) -> list[VariableDeclarationNode]:
        """Convert an assignment statement."""
        results = []
        value = self._convert_expression(node.value, source)

        for target in node.targets:
            if isinstance(target, ast.Name):
                results.append(
                    VariableDeclarationNode(
                        name=target.id,
                        initializer=value,
                        language=Language.PYTHON,
                    )
                )
        return results

    def _convert_annotated_assign(self, node: ast.AnnAssign, source: str) -> VariableDeclarationNode:
        """Convert an annotated assignment."""
        name = ""
        if isinstance(node.target, ast.Name):
            name = node.target.id

        var_type = self._get_annotation(node.annotation)
        value = self._convert_expression(node.value, source) if node.value else None

        return VariableDeclarationNode(
            name=name,
            variable_type=var_type,
            initializer=value,
            language=Language.PYTHON,
        )

    def _convert_return(self, node: ast.Return, source: str) -> ReturnStatementNode:
        """Convert a return statement."""
        value = self._convert_expression(node.value, source) if node.value else None
        return ReturnStatementNode(argument=value, language=Language.PYTHON)

    def _convert_if(self, node: ast.If, source: str) -> IfStatementNode:
        """Convert an if statement."""
        condition = self._convert_expression(node.test, source)
        consequent = self._convert_body(node.body, source)

        alternate: Optional[ASTNode] = None
        if node.orelse:
            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                alternate = self._convert_if(node.orelse[0], source)
            else:
                alternate = self._convert_body(node.orelse, source)

        return IfStatementNode(
            condition=condition,
            consequent=consequent,
            alternate=alternate,
            language=Language.PYTHON,
        )

    def _convert_for(self, node: ast.For, source: str) -> ForLoopNode:
        """Convert a for loop."""
        target = self._convert_expression(node.target, source)
        iter_expr = self._convert_expression(node.iter, source)
        body = self._convert_body(node.body, source)

        return ForLoopNode(
            initializer=target,
            condition=iter_expr,
            body=body,
            is_async=False,
            language=Language.PYTHON,
        )

    def _convert_async_for(self, node: ast.AsyncFor, source: str) -> ForLoopNode:
        """Convert an async for loop."""
        target = self._convert_expression(node.target, source)
        iter_expr = self._convert_expression(node.iter, source)
        body = self._convert_body(node.body, source)

        return ForLoopNode(
            initializer=target,
            condition=iter_expr,
            body=body,
            is_async=True,
            language=Language.PYTHON,
        )

    def _convert_while(self, node: ast.While, source: str) -> WhileLoopNode:
        """Convert a while loop."""
        condition = self._convert_expression(node.test, source)
        body = self._convert_body(node.body, source)

        return WhileLoopNode(
            condition=condition,
            body=body,
            language=Language.PYTHON,
        )

    def _convert_break(self, node: ast.Break, source: str) -> IdentifierNode:
        """Convert a break statement."""
        return IdentifierNode(name="break", language=Language.PYTHON)

    def _convert_continue(self, node: ast.Continue, source: str) -> IdentifierNode:
        """Convert a continue statement."""
        return IdentifierNode(name="continue", language=Language.PYTHON)

    def _convert_pass(self, node: ast.Pass, source: str) -> IdentifierNode:
        """Convert a pass statement."""
        return IdentifierNode(name="pass", language=Language.PYTHON)

    def _convert_raise(self, node: ast.Raise, source: str) -> IdentifierNode:
        """Convert a raise statement."""
        return IdentifierNode(name="raise", language=Language.PYTHON)

    def _convert_try(self, node: ast.Try, source: str) -> TryStatementNode:
        """Convert a try statement."""
        block = self._convert_body(node.body, source)

        handlers: list[CatchClauseNode] = []
        for handler in node.handlers:
            param = handler.name if handler.name else None
            body = self._convert_body(handler.body, source)
            handlers.append(
                CatchClauseNode(
                    parameter=param,
                    body=body,
                    language=Language.PYTHON,
                )
            )

        finalizer = self._convert_body(node.finalbody, source) if node.finalbody else None

        return TryStatementNode(
            block=block,
            handler=handlers[0] if handlers else None,
            finalizer=finalizer,
            language=Language.PYTHON,
        )

    def _convert_with(self, node: ast.With, source: str) -> BlockNode:
        """Convert a with statement."""
        return self._convert_body(node.body, source)

    def _convert_async_with(self, node: ast.AsyncWith, source: str) -> BlockNode:
        """Convert an async with statement."""
        return self._convert_body(node.body, source)

    def _convert_expr(self, node: ast.Expr, source: str) -> Optional[ASTNode]:
        """Convert an expression statement."""
        return self._convert_expression(node.value, source)

    def _convert_import(self, node: ast.Import, source: str) -> ImportNode:
        """Convert an import statement."""
        module_names = []
        for alias in node.names:
            module_names.append(alias.name)

        return ImportNode(
            module_name=module_names[0] if module_names else "",
            imported_names=module_names,
            language=Language.PYTHON,
        )

    def _convert_import_from(self, node: ast.ImportFrom, source: str) -> ImportNode:
        """Convert an import from statement."""
        module_name = node.module or ""
        imported_names = [alias.name for alias in node.names]

        return ImportNode(
            module_name=module_name,
            imported_names=imported_names,
            language=Language.PYTHON,
        )

    def _convert_global(self, node: ast.Global, source: str) -> IdentifierNode:
        """Convert a global statement."""
        return IdentifierNode(name="global", language=Language.PYTHON)

    def _convert_nonlocal(self, node: ast.Nonlocal, source: str) -> IdentifierNode:
        """Convert a nonlocal statement."""
        return IdentifierNode(name="nonlocal", language=Language.PYTHON)

    def _convert_assert(self, node: ast.Assert, source: str) -> IdentifierNode:
        """Convert an assert statement."""
        return IdentifierNode(name="assert", language=Language.PYTHON)

    def _convert_match(self, node: ast.Match, source: str) -> MatchStatementNode:
        """Convert a match statement."""
        expression = self._convert_expression(node.subject, source)
        cases: list[MatchCaseNode] = []

        for case in node.cases:
            pattern = self._convert_pattern(case.pattern, source)
            guard = self._convert_expression(case.guard, source) if case.guard else None
            body = self._convert_body(case.body, source)

            cases.append(
                MatchCaseNode(
                    pattern=pattern,
                    guard=guard,
                    body=body,
                    language=Language.PYTHON,
                )
            )

        return MatchStatementNode(
            expression=expression,
            cases=cases,
            language=Language.PYTHON,
        )

    def _convert_pattern(self, pattern: ast.pattern, source: str) -> IdentifierNode:
        """Convert a match pattern."""
        if isinstance(pattern, ast.MatchValue):
            return self._convert_expression(pattern.value, source) or IdentifierNode(name="pattern", language=Language.PYTHON)
        elif isinstance(pattern, ast.MatchClass):
            return IdentifierNode(name=pattern.cls.id if hasattr(pattern.cls, "id") else "class", language=Language.PYTHON)
        elif isinstance(pattern, ast.MatchSequence):
            return IdentifierNode(name="sequence", language=Language.PYTHON)
        elif isinstance(pattern, ast.MatchMapping):
            return IdentifierNode(name="mapping", language=Language.PYTHON)
        elif isinstance(pattern, ast.MatchStar):
            return IdentifierNode(name=f"*{pattern.name}", language=Language.PYTHON)
        elif isinstance(pattern, ast.MatchAs):
            return IdentifierNode(name=pattern.name or "_", language=Language.PYTHON)
        elif isinstance(pattern, ast.MatchOr):
            return IdentifierNode(name="or_pattern", language=Language.PYTHON)
        return IdentifierNode(name="pattern", language=Language.PYTHON)

    def _convert_delete(self, node: ast.Delete, source: str) -> IdentifierNode:
        """Convert a delete statement."""
        return IdentifierNode(name="del", language=Language.PYTHON)

    def _convert_name(self, node: ast.Name, source: str) -> IdentifierNode:
        """Convert a name expression."""
        return IdentifierNode(name=node.id, language=Language.PYTHON)

    def _convert_constant(self, node: ast.Constant, source: str) -> LiteralNode:
        """Convert a constant expression."""
        value = node.value
        literal_type = "string"

        if isinstance(value, bool):
            literal_type = "boolean"
        elif isinstance(value, (int, float)):
            literal_type = "number"
        elif value is None:
            literal_type = "None"

        return LiteralNode(
            value=value,
            raw_value=repr(value),
            literal_type=literal_type,
            language=Language.PYTHON,
        )

    def _convert_binop(self, node: ast.BinOp, source: str) -> BinaryOpNode:
        """Convert a binary operation."""
        operator_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",
            ast.Mod: "%",
            ast.Pow: "**",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
            ast.MatMult: "@",
        }

        left = self._convert_expression(node.left, source)
        right = self._convert_expression(node.right, source)
        operator = operator_map.get(type(node.op), str(node.op))

        return BinaryOpNode(
            operator=operator,
            left=left,
            right=right,
            language=Language.PYTHON,
        )

    def _convert_unaryop(self, node: ast.UnaryOp, source: str) -> UnaryOpNode:
        """Convert a unary operation."""
        operator_map = {
            ast.Invert: "~",
            ast.Not: "not",
            ast.UAdd: "+",
            ast.USub: "-",
        }

        operand = self._convert_expression(node.operand, source)
        operator = operator_map.get(type(node.op), str(node.op))

        return UnaryOpNode(
            operator=operator,
            operand=operand,
            language=Language.PYTHON,
        )

    def _convert_boolop(self, node: ast.BoolOp, source: str) -> BinaryOpNode:
        """Convert a boolean operation."""
        operator = "and" if isinstance(node.op, ast.And) else "or"
        left = self._convert_expression(node.values[0], source)
        right = self._convert_expression(node.values[1], source)

        return BinaryOpNode(
            operator=operator,
            left=left,
            right=right,
            language=Language.PYTHON,
        )

    def _convert_compare(self, node: ast.Compare, source: str) -> BinaryOpNode:
        """Convert a comparison."""
        operator_map = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Is: "is",
            ast.IsNot: "is not",
            ast.In: "in",
            ast.NotIn: "not in",
        }

        left = self._convert_expression(node.left, source)
        right = self._convert_expression(node.comparators[0], source)
        operator = operator_map.get(type(node.ops[0]), "==")

        return BinaryOpNode(
            operator=operator,
            left=left,
            right=right,
            language=Language.PYTHON,
        )

    def _convert_call(self, node: ast.Call, source: str) -> CallNode:
        """Convert a function call."""
        callee = self._convert_expression(node.func, source)
        arguments = []

        for arg in node.args:
            converted = self._convert_expression(arg, source)
            if converted:
                arguments.append(converted)

        # Handle keyword arguments
        for kwarg in node.keywords:
            if kwarg.arg:
                arguments.append(IdentifierNode(name=kwarg.arg, language=Language.PYTHON))

        return CallNode(
            callee=callee,
            arguments=arguments,
            language=Language.PYTHON,
        )

    def _convert_attribute(self, node: ast.Attribute, source: str) -> MemberAccessNode:
        """Convert an attribute access."""
        obj = self._convert_expression(node.value, source)

        return MemberAccessNode(
            object=obj,
            property_name=node.attr,
            language=Language.PYTHON,
        )

    def _convert_subscript(self, node: ast.Subscript, source: str) -> CallNode:
        """Convert a subscript operation."""
        obj = self._convert_expression(node.value, source)
        idx = self._convert_expression(node.slice, source)

        return CallNode(
            callee=obj,
            arguments=[idx] if idx else [],
            language=Language.PYTHON,
        )

    def _convert_list(self, node: ast.List, source: str) -> ArrayLiteralNode:
        """Convert a list literal."""
        elements = []
        for elt in node.elts:
            converted = self._convert_expression(elt, source)
            if converted:
                elements.append(converted)

        return ArrayLiteralNode(
            elements=elements,
            language=Language.PYTHON,
        )

    def _convert_tuple(self, node: ast.Tuple, source: str) -> ArrayLiteralNode:
        """Convert a tuple literal."""
        elements = []
        for elt in node.elts:
            converted = self._convert_expression(elt, source)
            if converted:
                elements.append(converted)

        return ArrayLiteralNode(
            elements=elements,
            language=Language.PYTHON,
        )

    def _convert_dict(self, node: ast.Dict, source: str) -> ObjectLiteralNode:
        """Convert a dict literal."""
        properties = []

        for key, value in zip(node.keys, node.values):
            key_node = self._convert_expression(key, source) if key else None
            value_node = self._convert_expression(value, source) if value else None

            if key_node:
                properties.append(
                    PropertyNode(
                        key=key_node,
                        value=value_node,
                        language=Language.PYTHON,
                    )
                )

        return ObjectLiteralNode(
            properties=properties,
            language=Language.PYTHON,
        )

    def _convert_set(self, node: ast.Set, source: str) -> ArrayLiteralNode:
        """Convert a set literal."""
        elements = []
        for elt in node.elts:
            converted = self._convert_expression(elt, source)
            if converted:
                elements.append(converted)

        return ArrayLiteralNode(
            elements=elements,
            language=Language.PYTHON,
        )

    def _convert_lambda(self, node: ast.Lambda, source: str) -> LambdaNode:
        """Convert a lambda expression."""
        parameters = self._convert_args(node.args, source)
        body = self._convert_expression(node.body, source)

        return LambdaNode(
            parameters=parameters,
            body=body or BlockNode(statements=[], language=Language.PYTHON),
            is_arrow=False,
            language=Language.PYTHON,
        )

    def _convert_ifexp(self, node: ast.IfExp, source: str) -> IfStatementNode:
        """Convert an if expression (ternary)."""
        condition = self._convert_expression(node.test, source)
        consequent = self._convert_expression(node.body, source)
        alternate = self._convert_expression(node.orelse, source)

        return IfStatementNode(
            condition=condition,
            consequent=consequent or BlockNode(statements=[], language=Language.PYTHON),
            alternate=alternate,
            language=Language.PYTHON,
        )

    def _convert_fstring(self, node: ast.JoinedStr, source: str) -> LiteralNode:
        """Convert a formatted string literal."""
        return LiteralNode(
            value=f'f"{source[node.col_offset:node.end_col_offset or len(source)]}"',
            raw_value=source[node.col_offset : node.end_col_offset or len(source)],
            literal_type="string",
            language=Language.PYTHON,
        )

    def _convert_slice(self, node: ast.Slice, source: str) -> IdentifierNode:
        """Convert a slice."""
        return IdentifierNode(name="slice", language=Language.PYTHON)

    def _convert_starred(self, node: ast.Starred, source: str) -> UnaryOpNode:
        """Convert a starred expression."""
        value = self._convert_expression(node.value, source)
        return UnaryOpNode(
            operator="*",
            operand=value or IdentifierNode(name="", language=Language.PYTHON),
            language=Language.PYTHON,
        )

    def _convert_yield(self, node: ast.Yield, source: str) -> ReturnStatementNode:
        """Convert a yield statement."""
        value = self._convert_expression(node.value, source) if node.value else None
        return ReturnStatementNode(argument=value, language=Language.PYTHON)

    def _convert_yieldfrom(self, node: ast.YieldFrom, source: str) -> ReturnStatementNode:
        """Convert a yield from statement."""
        value = self._convert_expression(node.value, source)
        return ReturnStatementNode(argument=value, language=Language.PYTHON)

    def _convert_await(self, node: ast.Await, source: str) -> UnaryOpNode:
        """Convert an await expression."""
        value = self._convert_expression(node.value, source)
        return UnaryOpNode(
            operator="await",
            operand=value or IdentifierNode(name="", language=Language.PYTHON),
            language=Language.PYTHON,
        )

    def _convert_formatted_value(self, node: ast.FormattedValue, source: str) -> IdentifierNode:
        """Convert a formatted value."""
        return IdentifierNode(name="formatted", language=Language.PYTHON)

    def _convert_args(self, node: ast.arguments, source: str) -> list[ParameterNode]:
        """Convert function arguments."""
        parameters: list[ParameterNode] = []

        for arg in node.posonlyargs + node.args:
            default = None
            if arg in node.defaults:
                idx = node.args.index(arg)
                default = self._convert_expression(node.defaults[idx], source)

            param = ParameterNode(
                name=arg.arg,
                parameter_type=self._get_annotation(arg.annotation),
                default_value=default,
                language=Language.PYTHON,
            )
            parameters.append(param)

        return parameters

    def _convert_body(self, body: list[ast.stmt], source: str) -> BlockNode:
        """Convert a list of statements to a block."""
        statements = []
        for stmt in body:
            converted = self._convert_statement(stmt, source)
            if converted:
                statements.append(converted)
        return BlockNode(statements=statements, language=Language.PYTHON)

    def _get_annotation(self, annotation: Optional[ast.expr]) -> Optional[TypeAnnotation]:
        """Get a type annotation from an AST node."""
        if not annotation:
            return None

        if isinstance(annotation, ast.Name):
            return TypeAnnotation(type_name=annotation.id)
        elif isinstance(annotation, ast.Constant):
            return TypeAnnotation(type_name=str(annotation.value))
        elif isinstance(annotation, ast.BinOp):
            # Handle Union types like str | int
            return TypeAnnotation(
                type_name="Union",
                is_union=True,
            )

        return None

    def _get_name_str(self, node: ast.expr) -> str:
        """Get the name string from an expression."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name_str(node.value)}.{node.attr}"
        return ""
