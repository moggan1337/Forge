"""
Base AST definitions and visitor pattern for Forge.

Provides common AST node types and the visitor pattern for traversing
and transforming code ASTs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Generic, TypeVar, Optional

from forge.transpiler.language import Language


T = TypeVar("T")


class NodeType(Enum):
    """Enumeration of all AST node types across languages."""

    # Program structure
    PROGRAM = auto()
    SOURCE_FILE = auto()
    MODULE = auto()
    BLOCK = auto()
    STATEMENT = auto()
    EXPRESSION = auto()

    # Declarations
    FUNCTION_DECL = auto()
    VARIABLE_DECL = auto()
    CLASS_DECL = auto()
    INTERFACE_DECL = auto()
    TRAIT_DECL = auto()
    STRUCT_DECL = auto()
    ENUM_DECL = auto()
    TYPE_ALIAS = auto()
    IMPORT = auto()
    EXPORT = auto()
    CONSTANT = auto()

    # Statements
    IF = auto()
    ELSE = auto()
    ELIF = auto()
    SWITCH = auto()
    CASE = auto()
    MATCH = auto()
    PATTERN = auto()
    FOR = auto()
    WHILE = auto()
    DO_WHILE = auto()
    LOOP = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    YIELD = auto()
    AWAIT = auto()
    THROW = auto()
    TRY = auto()
    CATCH = auto()
    FINALLY = auto()
    WITH = auto()
    ASSERT = auto()

    # Expressions
    BINARY_OP = auto()
    UNARY_OP = auto()
    CALL = auto()
    MEMBER_ACCESS = auto()
    INDEX_ACCESS = auto()
    SLICE = auto()
    TERNARY = auto()
    COALESCE = auto()
    OPTIONAL_CHAIN = auto()
    SPREAD = auto()
    REST = auto()
    LAMBDA = auto()
    ARROW_FUNCTION = auto()
    FUNCTION_EXPR = auto()
    NEW = auto()
    DELETE = auto()
    TYPE_OF = auto()
    VOID = auto()
    NAMED_ARG = auto()

    # Literals
    LITERAL = auto()
    IDENTIFIER = auto()
    STRING_LITERAL = auto()
    NUMERIC_LITERAL = auto()
    BOOLEAN_LITERAL = auto()
    NULL_LITERAL = auto()
    REGEX_LITERAL = auto()
    ARRAY_LITERAL = auto()
    OBJECT_LITERAL = auto()
    TUPLE_LITERAL = auto()

    # Types
    TYPE_ANNOTATION = auto()
    UNION_TYPE = auto()
    INTERSECTION_TYPE = auto()
    GENERIC_TYPE = auto()
    ARRAY_TYPE = auto()
    FUNCTION_TYPE = auto()
    OPTIONAL_TYPE = auto()
    NULLABLE_TYPE = auto()
    VOID_TYPE = auto()
    NEVER_TYPE = auto()
    ANY_TYPE = auto()
    UNKNOWN_TYPE = auto()
    TYPE_REFERENCE = auto()
    PRIMITIVE_TYPE = auto()

    # Class members
    PROPERTY = auto()
    METHOD = auto()
    CONSTRUCTOR = auto()
    GETTER = auto()
    SETTER = auto()
    PARAMETER = auto()
    PROPERTY_SIGNATURE = auto()
    METHOD_SIGNATURE = auto()
    INDEX_SIGNATURE = auto()
    CALL_SIGNATURE = auto()
    CONSTRUCTOR_SIGNATURE = auto()

    # Other
    COMMENT = auto()
    DECORATOR = auto()
    ATTRIBUTE = auto()
    ANNOTATION = auto()
    MODIFIER = auto()
    VISIBILITY = auto()
    GENERIC_PARAM = auto()
    WHERE_CLAUSE = auto()
    COMMA = auto()
    SEMICOLON = auto()
    DOT = auto()
    COLON = auto()
    QUESTION = auto()
    AMPERSAND = auto()
    PIPE = auto()
    UNKNOWN = auto()


@dataclass
class SourceLocation:
    """Represents a location in source code."""

    line: int
    column: int
    offset: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.line}:{self.column}"


@dataclass
class SourceRange:
    """Represents a range in source code."""

    start: SourceLocation
    end: SourceLocation

    @property
    def length(self) -> int:
        """Get the length of this range."""
        if self.end.offset is not None and self.start.offset is not None:
            return self.end.offset - self.start.offset
        return 0


@dataclass
class Comment:
    """Represents a code comment."""

    text: str
    is_block: bool
    range: SourceRange

    @property
    def prefix(self) -> str:
        """Get the comment prefix for the target language."""
        if self.is_block:
            return f"/* {self.text} */"
        return f"// {self.text}"


@dataclass
class Decorator:
    """Represents a decorator/attribute."""

    name: str
    arguments: list[Any] = field(default_factory=list)
    prefix: str = "@"


@dataclass
class Modifier:
    """Represents a modifier keyword."""

    name: str
    values: set[str] = field(default_factory=set)


@dataclass
class Documentation:
    """Represents documentation/comments attached to a node."""

    leading_comments: list[Comment] = field(default_factory=list)
    trailing_comment: Optional[Comment] = None
    jsdoc: Optional[str] = None
    docstring: Optional[str] = None

    @property
    def text(self) -> str:
        """Get combined documentation text."""
        parts = []
        if self.jsdoc:
            parts.append(self.jsdoc)
        if self.docstring:
            parts.append(self.docstring)
        for comment in self.leading_comments:
            parts.append(comment.text)
        return "\n".join(parts)


@dataclass
class TypeAnnotation:
    """Represents a type annotation."""

    type_name: str
    generic_params: list[TypeAnnotation] = field(default_factory=list)
    is_array: bool = False
    is_optional: bool = False
    is_nullable: bool = False
    is_union: bool = False
    union_types: list[TypeAnnotation] = field(default_factory=list)
    is_intersection: bool = False
    intersection_types: list[TypeAnnotation] = field(default_factory=list)
    default_value: Optional[str] = None


@dataclass
class ASTNode(ABC):
    """
    Abstract base class for all AST nodes.

    All concrete node types should inherit from this class and
    implement the `node_type` property.
    """

    node_type: NodeType
    language: Language
    source_range: Optional[SourceRange] = None
    documentation: Optional[Documentation] = None
    decorators: list[Decorator] = field(default_factory=list)
    modifiers: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    @abstractmethod
    def children(self) -> list[ASTNode]:
        """Get all child nodes."""
        ...

    @property
    @abstractmethod
    def source(self) -> str:
        """Get the original source code for this node."""
        ...

    def accept(self, visitor: ASTVisitor[T]) -> T:
        """Accept a visitor."""
        return visitor.visit(self)

    def find_children(self, node_type: NodeType) -> list[ASTNode]:
        """Find all children of a specific type."""
        results: list[ASTNode] = []
        for child in self.children:
            if child.node_type == node_type:
                results.append(child)
            results.extend(child.find_children(node_type))
        return results

    def find_parent(self, node_type: NodeType) -> Optional[ASTNode]:
        """Find the first parent of a specific type."""
        # This would require parent references - simplified for now
        return None


@dataclass
class ProgramNode(ASTNode):
    """Root node representing a complete program/source file."""

    body: list[ASTNode] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)  # Will be overridden
    source_code: str = ""

    @property
    def node_type(self) -> NodeType:
        return NodeType.PROGRAM

    @property
    def children(self) -> list[ASTNode]:
        return self.body

    @property
    def source(self) -> str:
        return self.source_code


@dataclass
class IdentifierNode(ASTNode):
    """Represents an identifier/name."""

    name: str
    language: Language = field(default=Language.PYTHON)
    source_code: str = ""

    @property
    def node_type(self) -> NodeType:
        return NodeType.IDENTIFIER

    @property
    def children(self) -> list[ASTNode]:
        return []

    @property
    def source(self) -> str:
        return self.source_code or self.name


@dataclass
class LiteralNode(ASTNode):
    """Represents a literal value."""

    value: Any
    raw_value: str
    literal_type: str = "string"
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.LITERAL

    @property
    def children(self) -> list[ASTNode]:
        return []

    @property
    def source(self) -> str:
        return self.raw_value


@dataclass
class BinaryOpNode(ASTNode):
    """Represents a binary operation."""

    operator: str
    left: ASTNode
    right: ASTNode
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.BINARY_OP

    @property
    def children(self) -> list[ASTNode]:
        return [self.left, self.right]

    @property
    def source(self) -> str:
        return f"{self.left.source} {self.operator} {self.right.source}"


@dataclass
class UnaryOpNode(ASTNode):
    """Represents a unary operation."""

    operator: str
    operand: ASTNode
    is_postfix: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.UNARY_OP

    @property
    def children(self) -> list[ASTNode]:
        return [self.operand]

    @property
    def source(self) -> str:
        if self.is_postfix:
            return f"{self.operand.source}{self.operator}"
        return f"{self.operator}{self.operand.source}"


@dataclass
class CallNode(ASTNode):
    """Represents a function call."""

    callee: ASTNode
    arguments: list[ASTNode] = field(default_factory=list)
    type_arguments: list[TypeAnnotation] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.CALL

    @property
    def children(self) -> list[ASTNode]:
        return [self.callee] + self.arguments

    @property
    def source(self) -> str:
        args_str = ", ".join(a.source for a in self.arguments)
        return f"{self.callee.source}({args_str})"


@dataclass
class MemberAccessNode(ASTNode):
    """Represents member access (property/attribute access)."""

    object: ASTNode
    property_name: str
    is_safe: bool = False  # ?. operator
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.MEMBER_ACCESS

    @property
    def children(self) -> list[ASTNode]:
        return [self.object]

    @property
    def source(self) -> str:
        operator = "?." if self.is_safe else "."
        return f"{self.object.source}{operator}{self.property_name}"


@dataclass
class FunctionDeclarationNode(ASTNode):
    """Represents a function declaration."""

    name: str
    parameters: list[ParameterNode] = field(default_factory=list)
    body: Optional[ASTNode] = None
    return_type: Optional[TypeAnnotation] = None
    is_async: bool = False
    is_generator: bool = False
    type_parameters: list[str] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.FUNCTION_DECL

    @property
    def children(self) -> list[ASTNode]:
        result = self.parameters
        if self.body:
            result.append(self.body)
        return result

    @property
    def source(self) -> str:
        params = ", ".join(p.source for p in self.parameters)
        return f"function {self.name}({params}) {{ ... }}"


@dataclass
class ParameterNode(ASTNode):
    """Represents a function parameter."""

    name: str
    parameter_type: Optional[TypeAnnotation] = None
    default_value: Optional[ASTNode] = None
    is_variadic: bool = False
    is_optional: bool = False
    is_positional_only: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.PARAMETER

    @property
    def children(self) -> list[ASTNode]:
        result = []
        if self.default_value:
            result.append(self.default_value)
        return result

    @property
    def source(self) -> str:
        parts = [self.name]
        if self.parameter_type:
            parts.append(f": {self.parameter_type.type_name}")
        if self.default_value:
            parts.append(f" = {self.default_value.source}")
        return "".join(parts)


@dataclass
class ClassDeclarationNode(ASTNode):
    """Represents a class declaration."""

    name: str
    base_classes: list[str] = field(default_factory=list)
    body: list[ASTNode] = field(default_factory=list)
    type_parameters: list[str] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.CLASS_DECL

    @property
    def children(self) -> list[ASTNode]:
        return self.body

    @property
    def source(self) -> str:
        bases = f" extends {', '.join(self.base_classes)}" if self.base_classes else ""
        return f"class {self.name}{bases} {{ ... }}"


@dataclass
class VariableDeclarationNode(ASTNode):
    """Represents a variable declaration."""

    name: str
    variable_type: Optional[TypeAnnotation] = None
    initializer: Optional[ASTNode] = None
    is_constant: bool = False
    is_readonly: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.VARIABLE_DECL

    @property
    def children(self) -> list[ASTNode]:
        if self.initializer:
            return [self.initializer]
        return []

    @property
    def source(self) -> str:
        parts = []
        if self.is_constant:
            parts.append("const ")
        parts.append(self.name)
        if self.variable_type:
            parts.append(f": {self.variable_type.type_name}")
        if self.initializer:
            parts.append(f" = {self.initializer.source}")
        return "".join(parts)


@dataclass
class IfStatementNode(ASTNode):
    """Represents an if/else statement."""

    condition: ASTNode
    consequent: ASTNode
    alternate: Optional[ASTNode] = None
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.IF

    @property
    def children(self) -> list[ASTNode]:
        result = [self.condition, self.consequent]
        if self.alternate:
            result.append(self.alternate)
        return result

    @property
    def source(self) -> str:
        result = f"if ({self.condition.source}) {{ ... }}"
        if self.alternate:
            result += f" else {{ ... }}"
        return result


@dataclass
class ReturnStatementNode(ASTNode):
    """Represents a return statement."""

    argument: Optional[ASTNode] = None
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.RETURN

    @property
    def children(self) -> list[ASTNode]:
        if self.argument:
            return [self.argument]
        return []

    @property
    def source(self) -> str:
        if self.argument:
            return f"return {self.argument.source}"
        return "return"


@dataclass
class ArrayLiteralNode(ASTNode):
    """Represents an array literal."""

    elements: list[ASTNode] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.ARRAY_LITERAL

    @property
    def children(self) -> list[ASTNode]:
        return self.elements

    @property
    def source(self) -> str:
        elements = ", ".join(e.source for e in self.elements)
        return f"[{elements}]"


@dataclass
class ObjectLiteralNode(ASTNode):
    """Represents an object literal."""

    properties: list[PropertyNode] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.OBJECT_LITERAL

    @property
    def children(self) -> list[ASTNode]:
        return [p.value for p in self.properties if p.value]

    @property
    def source(self) -> str:
        props = ", ".join(p.source for p in self.properties)
        return f"{{{props}}}"


@dataclass
class PropertyNode(ASTNode):
    """Represents an object property."""

    key: ASTNode
    value: Optional[ASTNode] = None
    computed: bool = False
    shorthand: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.PROPERTY

    @property
    def children(self) -> list[ASTNode]:
        if self.value:
            return [self.key, self.value]
        return [self.key]

    @property
    def source(self) -> str:
        if self.shorthand:
            return self.key.source
        if self.value:
            computed_l = "[" if self.computed else ""
            computed_r = "]" if self.computed else ""
            return f"{computed_l}{self.key.source}{computed_r}: {self.value.source}"
        return self.key.source


@dataclass
class ImportNode(ASTNode):
    """Represents an import statement."""

    module_name: str
    imported_names: list[str] = field(default_factory=list)
    is_default: bool = False
    is_namespace: bool = False
    alias: Optional[str] = None
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.IMPORT

    @property
    def children(self) -> list[ASTNode]:
        return []

    @property
    def source(self) -> str:
        if self.is_namespace:
            return f"import * as {self.alias or 'ns'} from '{self.module_name}'"
        if self.is_default:
            name = self.imported_names[0] if self.imported_names else "default"
            alias = f" as {self.alias}" if self.alias else ""
            return f"import {name}{alias} from '{self.module_name}'"
        names = ", ".join(self.imported_names)
        return f"import {{{names}}} from '{self.module_name}'"


@dataclass
class ExportNode(ASTNode):
    """Represents an export statement."""

    exported_name: str
    exported_node: Optional[ASTNode] = None
    is_default: bool = False
    is_re_export: bool = False
    module_name: Optional[str] = None
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.EXPORT

    @property
    def children(self) -> list[ASTNode]:
        if self.exported_node:
            return [self.exported_node]
        return []

    @property
    def source(self) -> str:
        if self.is_default:
            return f"export default {self.exported_name}"
        return f"export {self.exported_name}"


@dataclass
class TryStatementNode(ASTNode):
    """Represents a try/catch statement."""

    block: ASTNode
    handler: Optional[ASTNode] = None
    finalizer: Optional[ASTNode] = None
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.TRY

    @property
    def children(self) -> list[ASTNode]:
        result = [self.block]
        if self.handler:
            result.append(self.handler)
        if self.finalizer:
            result.append(self.finalizer)
        return result

    @property
    def source(self) -> str:
        result = "try { ... }"
        if self.handler:
            result += " catch { ... }"
        if self.finalizer:
            result += " finally { ... }"
        return result


@dataclass
class CatchClauseNode(ASTNode):
    """Represents a catch clause."""

    parameter: Optional[str] = None
    body: ASTNode
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.CATCH

    @property
    def children(self) -> list[ASTNode]:
        return [self.body]

    @property
    def source(self) -> str:
        param = f"({self.parameter})" if self.parameter else ""
        return f"catch{param} {{ ... }}"


@dataclass
class MatchStatementNode(ASTNode):
    """Represents a match/switch statement."""

    expression: ASTNode
    cases: list[MatchCaseNode] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.MATCH

    @property
    def children(self) -> list[ASTNode]:
        return [self.expression] + [c.body for c in self.cases]

    @property
    def source(self) -> str:
        return f"match ({self.expression.source}) {{ ... }}"


@dataclass
class MatchCaseNode(ASTNode):
    """Represents a case in a match/switch."""

    pattern: ASTNode
    guard: Optional[ASTNode] = None
    body: ASTNode
    is_default: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.CASE

    @property
    def children(self) -> list[ASTNode]:
        result = [self.pattern]
        if self.guard:
            result.append(self.guard)
        result.append(self.body)
        return result

    @property
    def source(self) -> str:
        return f"case {self.pattern.source}: ..."


@dataclass
class ForLoopNode(ASTNode):
    """Represents a for loop."""

    initializer: Optional[ASTNode] = None
    condition: Optional[ASTNode] = None
    update: Optional[ASTNode] = None
    body: ASTNode
    is_async: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.FOR

    @property
    def children(self) -> list[ASTNode]:
        result = []
        if self.initializer:
            result.append(self.initializer)
        if self.condition:
            result.append(self.condition)
        if self.update:
            result.append(self.update)
        result.append(self.body)
        return result

    @property
    def source(self) -> str:
        return "for (...) { ... }"


@dataclass
class WhileLoopNode(ASTNode):
    """Represents a while loop."""

    condition: ASTNode
    body: ASTNode
    is_do_while: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.WHILE

    @property
    def children(self) -> list[ASTNode]:
        return [self.condition, self.body]

    @property
    def source(self) -> str:
        if self.is_do_while:
            return "do { ... } while (...)"
        return "while (...) { ... }"


@dataclass
class LambdaNode(ASTNode):
    """Represents a lambda/arrow function."""

    parameters: list[ParameterNode] = field(default_factory=list)
    body: ASTNode
    is_arrow: bool = True
    is_async: bool = False
    return_type: Optional[TypeAnnotation] = None
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.ARROW_FUNCTION

    @property
    def children(self) -> list[ASTNode]:
        return self.parameters + [self.body]

    @property
    def source(self) -> str:
        params = ", ".join(p.source for p in self.parameters)
        if self.is_arrow:
            return f"({params}) => {{ ... }}"
        return f"lambda {params}: ..."


@dataclass
class BlockNode(ASTNode):
    """Represents a block of statements."""

    statements: list[ASTNode] = field(default_factory=list)
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.BLOCK

    @property
    def children(self) -> list[ASTNode]:
        return self.statements

    @property
    def source(self) -> str:
        return "{ ... }"


@dataclass
class CommentNode(ASTNode):
    """Represents a comment."""

    text: str
    is_block: bool = False
    language: Language = field(default=Language.PYTHON)

    @property
    def node_type(self) -> NodeType:
        return NodeType.COMMENT

    @property
    def children(self) -> list[ASTNode]:
        return []

    @property
    def source(self) -> str:
        if self.is_block:
            return f"/* {self.text} */"
        return f"// {self.text}"


@dataclass
class ParseResult:
    """Result of parsing source code."""

    success: bool
    ast: Optional[ProgramNode] = None
    errors: list[ParseError] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)
    source_code: str = ""
    language: Language = Language.PYTHON

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there were any warnings."""
        return len(self.warnings) > 0


@dataclass
class ParseError:
    """Represents a parsing error."""

    message: str
    line: int
    column: int
    length: int = 0

    def __str__(self) -> str:
        return f"Parse error at line {self.line}, column {self.column}: {self.message}"


@dataclass
class ParseWarning:
    """Represents a parsing warning."""

    message: str
    line: int
    column: int
    length: int = 0


class ASTVisitor(ABC, Generic[T]):
    """Abstract visitor for traversing AST nodes."""

    @abstractmethod
    def visit(self, node: ASTNode) -> T:
        """Visit a node."""
        ...

    def visit_program(self, node: ProgramNode) -> T:
        """Visit a program node."""
        return self.visit_children(node)

    def visit_identifier(self, node: IdentifierNode) -> T:
        """Visit an identifier node."""
        return self.visit(node)

    def visit_literal(self, node: LiteralNode) -> T:
        """Visit a literal node."""
        return self.visit(node)

    def visit_binary_op(self, node: BinaryOpNode) -> T:
        """Visit a binary operation node."""
        left = node.left.accept(self)
        right = node.right.accept(self)
        return self.visit(node)

    def visit_unary_op(self, node: UnaryOpNode) -> T:
        """Visit a unary operation node."""
        operand = node.operand.accept(self)
        return self.visit(node)

    def visit_call(self, node: CallNode) -> T:
        """Visit a call node."""
        callee = node.callee.accept(self)
        for arg in node.arguments:
            arg.accept(self)
        return self.visit(node)

    def visit_member_access(self, node: MemberAccessNode) -> T:
        """Visit a member access node."""
        obj = node.object.accept(self)
        return self.visit(node)

    def visit_function(self, node: FunctionDeclarationNode) -> T:
        """Visit a function declaration node."""
        for param in node.parameters:
            param.accept(self)
        if node.body:
            node.body.accept(self)
        return self.visit(node)

    def visit_class(self, node: ClassDeclarationNode) -> T:
        """Visit a class declaration node."""
        for member in node.body:
            member.accept(self)
        return self.visit(node)

    def visit_variable(self, node: VariableDeclarationNode) -> T:
        """Visit a variable declaration node."""
        if node.initializer:
            node.initializer.accept(self)
        return self.visit(node)

    def visit_if(self, node: IfStatementNode) -> T:
        """Visit an if statement node."""
        node.condition.accept(self)
        node.consequent.accept(self)
        if node.alternate:
            node.alternate.accept(self)
        return self.visit(node)

    def visit_return(self, node: ReturnStatementNode) -> T:
        """Visit a return statement node."""
        if node.argument:
            node.argument.accept(self)
        return self.visit(node)

    def visit_children(self, node: ASTNode) -> T:
        """Visit all children of a node."""
        for child in node.children:
            child.accept(self)
        return self.visit(node)
