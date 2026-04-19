"""
LSP protocol types for Forge.

Defines the types and structures used in the Language Server Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union


class LSPRequest:
    """Base class for LSP requests."""

    def __init__(
        self,
        jsonrpc: str = "2.0",
        id: Optional[Union[int, str]] = None,
        method: str = "",
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        self.jsonrpc = jsonrpc
        self.id = id
        self.method = method
        self.params = params or {}


class LSPResponse:
    """Base class for LSP responses."""

    def __init__(
        self,
        jsonrpc: str = "2.0",
        id: Optional[Union[int, str]] = None,
        result: Optional[Any] = None,
        error: Optional[dict[str, Any]] = None,
    ) -> None:
        self.jsonrpc = jsonrpc
        self.id = id
        self.result = result
        self.error = error


class LSPNotification:
    """Base class for LSP notifications."""

    def __init__(
        self,
        jsonrpc: str = "2.0",
        method: str = "",
        params: Optional[dict[str, Any]] = None,
    ) -> None:
        self.jsonrpc = jsonrpc
        self.method = method
        self.params = params or {}


@dataclass
class TextDocumentItem:
    """A text document with URI and optional content."""

    uri: str
    languageId: Optional[str] = None
    version: Optional[int] = None
    text: str = ""


@dataclass
class Position:
    """A position in a text document."""

    line: int
    character: int

    def __str__(self) -> str:
        return f"{self.line}:{self.character}"


@dataclass
class Range:
    """A range in a text document."""

    start: Position
    end: Position

    def __str__(self) -> str:
        return f"{self.start} - {self.end}"


@dataclass
class Location:
    """A location in a text document."""

    uri: str
    range: Range


@dataclass
class DiagnosticRelatedInformation:
    """Related diagnostic information."""

    location: Location
    message: str


@dataclass
class Diagnostic:
    """A diagnostic (error, warning, info) in a text document."""

    range: Range
    severity: int
    code: Optional[Union[int, str]] = None
    source: Optional[str] = None
    message: str
    relatedInformation: Optional[list[DiagnosticRelatedInformation]] = None


class DiagnosticSeverity(Enum):
    """Diagnostic severity levels."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass
class TextEdit:
    """A text edit to apply to a document."""

    range: Range
    newText: str


@dataclass
class CompletionItem:
    """A completion item."""

    label: str
    kind: Optional[int] = None
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insertText: Optional[str] = None
    insertTextFormat: Optional[int] = None
    textEdit: Optional[TextEdit] = None
    commitCharacters: Optional[list[str]] = None
    data: Optional[dict[str, Any]] = None


@dataclass
class Hover:
    """Hover information."""

    contents: Union[str, dict[str, Any]]
    range: Optional[Range] = None


@dataclass
class SignatureInformation:
    """Information about a function signature."""

    label: str
    documentation: Optional[str] = None
    parameters: Optional[list[dict[str, Any]]] = None


@dataclass
class SignatureHelp:
    """Signature help information."""

    signatures: list[SignatureInformation]
    activeSignature: Optional[int] = None
    activeParameter: Optional[int] = None


@dataclass
class WorkspaceEdit:
    """A workspace edit."""

    changes: Optional[dict[str, list[TextEdit]]] = None
    documentChanges: Optional[list[Any]] = None


@dataclass
class SymbolInformation:
    """Information about a symbol."""

    name: str
    kind: int
    location: Location
    containerName: Optional[str] = None
    deprecated: Optional[bool] = None


@dataclass
class DocumentSymbol:
    """A symbol in a document."""

    name: str
    kind: int
    range: Range
    selectionRange: Range
    children: Optional[list[DocumentSymbol]] = None
    detail: Optional[str] = None
    deprecated: Optional[bool] = None


@dataclass
class CallHierarchyItem:
    """A call hierarchy item."""

    name: str
    kind: int
    uri: str
    range: Range
    selectionRange: Range


@dataclass
class CallHierarchyIncomingCall:
    """An incoming call to a call hierarchy item."""

    from_: CallHierarchyItem = field(compare=False)
    fromRanges: list[Range] = field(default_factory=list)
