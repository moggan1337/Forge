"""
LSP server implementation for Forge.

Provides Language Server Protocol support for IDE integration.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
from pathlib import Path
from typing import Any, Callable, Optional

from forge.transpiler.core import Transpiler, TranspilerConfig
from forge.transpiler.language import Language
from forge.lsp.protocol import (
    LSPRequest,
    LSPResponse,
    TextDocumentItem,
    Position,
    Range,
    Diagnostic,
    DiagnosticSeverity,
)


logger = logging.getLogger(__name__)


class LSPServer:
    """
    Language Server Protocol server for Forge.

    Implements a subset of the LSP specification for providing
    transpilation features in compatible IDEs.
    """

    def __init__(self, host: str = "localhost", port: int = 8765) -> None:
        """
        Initialize the LSP server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Document store
        self._documents: dict[str, str] = {}

        # Transpilers for different language pairs
        self._transpilers: dict[str, Transpiler] = {}

        # Capabilities
        self._capabilities = {
            "textDocumentSync": 1,  # Full sync
            "hoverProvider": True,
            "completionProvider": {
                "resolveProvider": False,
            },
            "workspaceSymbolProvider": True,
        }

    def run(self) -> None:
        """Start the LSP server."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.listen(1)

        logger.info(f"LSP server listening on {self.host}:{self.port}")

        self._running = True

        while self._running:
            try:
                conn, addr = self._socket.accept()
                logger.info(f"Client connected from {addr}")

                # Handle client in a thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn,),
                    daemon=True,
                )
                client_thread.start()

            except Exception as e:
                if self._running:
                    logger.error(f"Accept error: {e}")

    def _handle_client(self, conn: socket.socket) -> None:
        """Handle a client connection."""
        try:
            while self._running:
                # Read message header
                headers = {}
                while True:
                    line = conn.recv(1024).decode("utf-8")
                    if not line:
                        return
                    if line == "\r\n":
                        break
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

                # Read body
                content_length = int(headers.get("content-length", 0))
                if content_length > 0:
                    body = b""
                    while len(body) < content_length:
                        body += conn.recv(content_length - len(body))
                else:
                    body = b""

                # Parse request
                try:
                    request = json.loads(body.decode("utf-8"))
                    response = self._handle_request(request)

                    if response:
                        self._send_response(conn, response)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")

        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            conn.close()

    def _handle_request(self, request: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Handle an LSP request."""
        method = request.get("method", "")

        # Handle requests
        handlers: dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "textDocument/didOpen": self._handle_text_document_did_open,
            "textDocument/didChange": self._handle_text_document_did_change,
            "textDocument/didClose": self._handle_text_document_did_close,
            "textDocument/hover": self._handle_hover,
            "textDocument/completion": self._handle_completion,
            "textDocument/diagnostic": self._handle_diagnostic,
            "forge/transpile": self._handle_transpile,
            "shutdown": self._handle_shutdown,
        }

        handler = handlers.get(method)
        if handler:
            try:
                result = handler(request.get("params", {}))
                if "id" in request:
                    return {
                        "jsonrpc": "2.0",
                        "id": request["id"],
                        "result": result,
                    }
                return None
            except Exception as e:
                logger.error(f"Handler error for {method}: {e}")
                if "id" in request:
                    return {
                        "jsonrpc": "2.0",
                        "id": request["id"],
                        "error": {
                            "code": -32603,
                            "message": str(e),
                        },
                    }
        else:
            # Send notification acknowledgment
            if "id" not in request:
                return None

            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": None,
            }

    def _send_response(self, conn: socket.socket, response: dict[str, Any]) -> None:
        """Send an LSP response."""
        body = json.dumps(response).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n"
        conn.sendall(header.encode("utf-8") + body)

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialize request."""
        return {
            "capabilities": self._capabilities,
            "serverInfo": {
                "name": "Forge",
                "version": "0.1.0",
            },
        }

    def _handle_text_document_did_open(self, params: dict[str, Any]) -> None:
        """Handle textDocument/didOpen notification."""
        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")
        text = text_doc.get("text", "")

        self._documents[uri] = text
        logger.debug(f"Opened document: {uri}")

    def _handle_text_document_did_change(self, params: dict[str, Any]) -> None:
        """Handle textDocument/didChange notification."""
        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")
        changes = params.get("contentChanges", [])

        if uri in self._documents:
            # For full sync, just use the last change
            if changes:
                self._documents[uri] = changes[-1].get("text", "")

        logger.debug(f"Changed document: {uri}")

    def _handle_text_document_did_close(self, params: dict[str, Any]) -> None:
        """Handle textDocument/didClose notification."""
        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")

        if uri in self._documents:
            del self._documents[uri]

        logger.debug(f"Closed document: {uri}")

    def _handle_hover(self, params: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Handle textDocument/hover request."""
        text_doc = params.get("textDocument", {})
        position = params.get("position", {})

        uri = text_doc.get("uri", "")
        if uri not in self._documents:
            return None

        text = self._documents[uri]
        line = position.get("line", 0)
        char = position.get("character", 0)

        # Find word at position
        lines = text.split("\n")
        if line < len(lines):
            line_text = lines[line]
            if char < len(line_text):
                # Simple word detection
                start = char
                end = char
                while start > 0 and line_text[start - 1].isalnum():
                    start -= 1
                while end < len(line_text) and line_text[end].isalnum():
                    end += 1
                word = line_text[start:end]

                if word:
                    return {
                        "contents": {
                            "kind": "markdown",
                            "value": f"**{word}**\n\nType information would appear here.",
                        }
                    }

        return None

    def _handle_completion(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Handle textDocument/completion request."""
        # Return basic completions
        keywords = [
            "function", "class", "interface", "type", "enum",
            "const", "let", "var", "if", "else", "for", "while",
            "return", "import", "export", "from",
        ]

        return [
            {
                "label": kw,
                "kind": 14,  # Keyword
            }
            for kw in keywords
        ]

    def _handle_diagnostic(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle textDocument/diagnostic request."""
        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "")

        # Return empty diagnostics (no linting implemented)
        return {"items": []}

    def _handle_transpile(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle forge/transpile request (custom method)."""
        source_uri = params.get("sourceUri", "")
        target_lang = params.get("targetLanguage", "python")

        if source_uri not in self._documents:
            return {"error": "Document not found"}

        source_code = self._documents[source_uri]

        # Detect source language from URI
        path = Path(source_uri)
        ext = path.suffix.lower()
        source_lang = Language.from_extension(ext) or Language.TYPESCRIPT
        target_language = Language.from_string(target_lang) or Language.PYTHON

        # Transpile
        config = TranspilerConfig(
            source_language=source_lang,
            target_language=target_language,
            use_llm=False,
        )
        transpiler = Transpiler(config)
        result = transpiler.transpile(source_code)

        if result.success:
            return {
                "success": True,
                "output": result.output,
                "sourceLanguage": source_lang.value,
                "targetLanguage": target_language.value,
            }
        else:
            return {
                "success": False,
                "errors": result.errors,
            }

    def _handle_shutdown(self, params: dict[str, Any]) -> None:
        """Handle shutdown request."""
        self._running = False

    def stop(self) -> None:
        """Stop the LSP server."""
        self._running = False
        if self._socket:
            self._socket.close()


def start_server(host: str = "localhost", port: int = 8765) -> LSPServer:
    """
    Start an LSP server.

    Args:
        host: Host to bind to
        port: Port to listen on

    Returns:
        The running LSPServer instance
    """
    server = LSPServer(host=host, port=port)
    server.run()
    return server
