# Forge - AI-Assisted Language Transpiler

Forge is an intelligent, AI-powered code transpiler that converts source code between programming languages while preserving semantics, idioms, and best practices of the target language.

## Supported Languages

| Language | Parser | Status | Type System |
|----------|--------|--------|-------------|
| TypeScript | @typescript-eslint/typescript-estree | ✅ Stable | Structural |
| Python | ast (built-in) | ✅ Stable | Duck Typed |
| Rust | syn + quote | ✅ Stable | Ownership |
| Go | go/parser | ✅ Stable | Structural |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Forge Core                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Parser    │  │   AST       │  │   Type System       │ │
│  │   Layer     │→ │   Normalizer│→ │   Mapper            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         ↓                                    ↓              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LLM Translation Engine                  │   │
│  │  (Context-aware, idiomatic output generation)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Formatter  │  │  Builder    │  │   LSP Server        │ │
│  │  Preserver  │  │  Verifier   │  │   (Language Server) │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

1. **AST-Based Parsing**: Deep code analysis using language-specific parsers
2. **LLM-Assisted Translation**: Context-aware, idiomatic code generation
3. **Type System Mapping**: Intelligent type conversions between languages
4. **Comment Preservation**: Maintains comments, formatting, and structure
5. **Build Verification**: Compiles and tests transpiled code
6. **LSP Integration**: Full language server protocol support

## Installation

```bash
pip install forge-transpiler
# or
npm install -g forge-transpiler
```

## Usage

```bash
# Basic transpilation
forge transpile input.ts --output main.py

# With LLM assistance
forge transpile input.ts --output main.py --llm --model gpt-4

# LSP server mode
forge lsp --port 8765

# Build verification
forge verify output.go --language go
```

## License

MIT
