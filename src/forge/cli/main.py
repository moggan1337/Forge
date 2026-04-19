"""
Main CLI entry point for Forge.

Provides a rich command-line interface for code transpilation.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from forge import __version__
from forge.llm.llm_config import LLMConfig, LLMProvider
from forge.transpiler.core import Transpiler, TranspilerConfig
from forge.transpiler.language import Language, LanguagePair, get_language_pair, get_supported_pairs


console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="forge")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Forge - AI-Assisted Language Transpiler

    Convert code between programming languages with intelligent,
    context-aware translation powered by LLMs.
    """
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(
            "[bold cyan]Forge[/bold cyan] - AI-Assisted Language Transpiler\n\n"
            "[dim]Version:[/dim] [green]{version}[/green]\n"
            "[dim]Supported Languages:[/dim] TypeScript, Python, Rust, Go\n\n"
            "[dim]Usage:[/dim] forge [COMMAND] [OPTIONS]\n"
            "[dim]Example:[/dim] forge transpile input.ts -o output.py\n\n"
            "[dim]Run 'forge --help' for more information.[/dim]"
        ).format(version=__version__))


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path (default: stdout)"
)
@click.option(
    "-s", "--source-lang",
    type=click.Choice(["typescript", "python", "rust", "go", "javascript"]),
    default=None,
    help="Source language (auto-detected from extension if not specified)"
)
@click.option(
    "-t", "--target-lang",
    type=click.Choice(["typescript", "python", "rust", "go"]),
    required=True,
    help="Target language"
)
@click.option(
    "--llm/--no-llm",
    default=False,
    help="Use LLM assistance for better translation"
)
@click.option(
    "--model",
    type=str,
    default="gpt-4",
    help="LLM model to use (when --llm is enabled)"
)
@click.option(
    "--api-key",
    type=str,
    default=None,
    help="API key for LLM provider"
)
@click.option(
    "--preserve-comments/--no-comments",
    default=True,
    help="Preserve comments from source"
)
@click.option(
    "--add-header/--no-header",
    default=True,
    help="Add transpilation header comment"
)
@click.option(
    "--verify/--no-verify",
    default=True,
    help="Verify output compiles"
)
def transpile(
    input_file: str,
    output: Optional[str],
    source_lang: Optional[str],
    target_lang: str,
    llm: bool,
    model: str,
    api_key: Optional[str],
    preserve_comments: bool,
    add_header: bool,
    verify: bool,
) -> None:
    """
    Transpile source code from one language to another.

    Examples:

        forge transpile input.ts -t python -o output.py

        forge transpile main.rs --target-lang typescript --llm
    """
    # Determine languages
    input_path = Path(input_file)

    if source_lang:
        source_language = Language.from_string(source_lang)
        if not source_language:
            console.print(f"[red]Error:[/red] Invalid source language: {source_lang}")
            sys.exit(1)
    else:
        ext = input_path.suffix.lower()
        source_language = Language.from_extension(ext)
        if not source_language:
            console.print(f"[red]Error:[/red] Could not detect language from extension: {ext}")
            sys.exit(1)

    target_language = Language.from_string(target_lang)
    if not target_language:
        console.print(f"[red]Error:[/red] Invalid target language: {target_lang}")
        sys.exit(1)

    if source_language == target_language:
        console.print("[yellow]Warning:[/yellow] Source and target languages are the same.")
        sys.exit(0)

    # Get language pair info
    pair = get_language_pair(source_language, target_language)

    # Read input
    console.print(f"\n[dim]Reading {input_file}...[/dim]")
    with open(input_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Configure transpiler
    llm_config = None
    if llm:
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model=model,
            api_key=api_key,
            enabled=True,
        )

    config = TranspilerConfig(
        source_language=source_language,
        target_language=target_language,
        use_llm=llm,
        llm_config=llm_config,
        preserve_comments=preserve_comments,
        add_header=add_header,
        verify_output=verify,
    )

    # Show info
    table = Table(show_header=False, box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Source", source_language.display_name)
    table.add_row("Target", target_language.display_name)
    table.add_row("Difficulty", f"{pair.difficulty}/5")
    table.add_row("LLM", "Enabled" if llm else "Disabled")
    console.print(table)
    console.print()

    # Transpile
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Transpiling...", total=None)

        transpiler = Transpiler(config)
        result = transpiler.transpile(source_code)

    # Handle result
    if result.success:
        console.print("[green]✓[/green] Transpilation successful!")

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.output)
            console.print(f"[dim]Written to {output}[/dim]")
        else:
            console.print("\n[bold]Output:[/bold]")
            syntax = Syntax(result.output, target_lang, theme="monokai", line_numbers=True)
            console.print(syntax)

        # Show metrics
        if result.metrics:
            console.print("\n[dim]Metrics:[/dim]")
            for key, value in result.metrics.items():
                console.print(f"  [dim]{key}:[/dim] {value}")

    else:
        console.print("[red]✗[/red] Transpilation failed!")
        for error in result.errors:
            console.print(f"  [red]Error:[/red] {error}")
        sys.exit(1)

    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]Warning:[/yellow] {warning}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output file path"
)
@click.option(
    "-t", "--target-lang",
    type=click.Choice(["typescript", "python", "rust", "go"]),
    required=True,
    help="Target language"
)
def analyze(input_file: str, output: Optional[str], target_lang: str) -> None:
    """
    Analyze source code and show type mappings.

    This command parses the source code and displays information about
    types, functions, and other constructs that will be mapped during
    transpilation.
    """
    input_path = Path(input_file)
    ext = input_path.suffix.lower()

    source_language = Language.from_extension(ext)
    if not source_language:
        console.print(f"[red]Error:[/red] Could not detect language from extension: {ext}")
        sys.exit(1)

    target_language = Language.from_string(target_lang)
    if not target_language:
        console.print(f"[red]Error:[/red] Invalid target language: {target_lang}")
        sys.exit(1)

    # Read input
    with open(input_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Parse
    from forge.parsers import TypeScriptParser, PythonParser, RustParser, GoParser

    parsers = {
        Language.TYPESCRIPT: TypeScriptParser(),
        Language.PYTHON: PythonParser(),
        Language.RUST: RustParser(),
        Language.GO: GoParser(),
    }

    parser = parsers.get(source_language)
    if not parser:
        console.print(f"[red]Error:[/red] No parser for {source_language.display_name}")
        sys.exit(1)

    result = parser.parse(source_code)

    if not result.success:
        console.print("[red]Parse errors:[/red]")
        for error in result.errors:
            console.print(f"  {error}")
        sys.exit(1)

    console.print(f"\n[bold]Analysis of {input_file}[/bold]")
    console.print(f"[dim]Language: {source_language.display_name}[/dim]\n")

    # Show AST structure
    if result.ast:
        console.print("[bold cyan]AST Structure:[/bold cyan]")

        def show_node(node, indent=0):
            from forge.parsers.base import ProgramNode
            prefix = "  " * indent
            name = type(node).__name__.replace("Node", "")

            if hasattr(node, "name"):
                console.print(f"{prefix}[yellow]{name}[/yellow]: {node.name}")
            elif isinstance(node, ProgramNode):
                console.print(f"{prefix}[yellow]{name}[/yellow]")
            else:
                console.print(f"{prefix}[yellow]{name}[/yellow]")

            for child in node.children[:5]:  # Limit children shown
                show_node(child, indent + 1)
            if len(node.children) > 5:
                console.print(f"{prefix}  ... and {len(node.children) - 5} more")

        show_node(result.ast)

    # Show type mappings
    from forge.types import TypeMapper
    mapper = TypeMapper()

    console.print("\n[bold cyan]Type Mappings:[/bold cyan]")
    console.print(f"[dim]Mapping from {source_language.display_name} to {target_language.display_name}:[/dim]\n")

    # Sample mappings
    sample_types = {
        Language.TYPESCRIPT: ["string", "number", "boolean", "Array<T>", "Promise<T>"],
        Language.PYTHON: ["str", "int", "bool", "List[T]", "Optional[T]"],
        Language.RUST: ["String", "i32", "bool", "Vec<T>", "Option<T>"],
        Language.GO: ["string", "int", "bool", "[]T", "interface{}"],
    }

    if source_language in sample_types:
        table = Table(show_header=True)
        table.add_column("Source Type", style="cyan")
        table.add_column("Target Type", style="green")
        table.add_column("Quality", style="yellow")

        for type_name in sample_types[source_language]:
            mapping = mapper.map_type(type_name, source_language, target_language)
            quality_color = {
                "exact": "green",
                "close": "yellow",
                "approximate": "red",
            }.get(mapping.quality, "white")
            table.add_row(type_name, mapping.target_type, f"[{quality_color}]{mapping.quality}[/{quality_color}]")

        console.print(table)


@cli.command("list-pairs")
def list_pairs() -> None:
    """
    List all supported language pairs and their difficulty levels.
    """
    pairs = get_supported_pairs()

    table = Table(show_header=True, title="Supported Language Pairs")
    table.add_column("Source", style="cyan")
    table.add_column("Target", style="green")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Notes", style="dim")

    for pair in sorted(pairs, key=lambda p: p.source.display_name):
        difficulty_bar = "●" * pair.difficulty + "○" * (5 - pair.difficulty)
        table.add_row(
            pair.source.display_name,
            pair.target.display_name,
            difficulty_bar,
            pair.notes[:50] + "..." if len(pair.notes) > 50 else pair.notes,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(pairs)} supported language pairs[/dim]")


@cli.command()
@click.option(
    "--port",
    type=int,
    default=8765,
    help="Port to listen on"
)
@click.option(
    "--host",
    type=str,
    default="localhost",
    help="Host to bind to"
)
def lsp(port: int, host: str) -> None:
    """
    Start the Forge Language Server Protocol (LSP) server.

    This enables IDE integration for transpilation features.
    """
    console.print(f"[cyan]Starting Forge LSP server on {host}:{port}...[/cyan]")

    try:
        from forge.lsp.server import LSPServer
        server = LSPServer(host=host, port=port)
        server.run()
    except ImportError:
        console.print("[yellow]Warning:[/yellow] LSP server requires additional dependencies.")
        console.print("Install with: pip install forge-transpiler[lsp]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to start LSP server: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--api-key",
    type=str,
    default=None,
    help="OpenAI API key"
)
@click.option(
    "--provider",
    type=click.Choice(["openai", "anthropic"]),
    default="openai",
    help="LLM provider"
)
def configure(api_key: Optional[str], provider: str) -> None:
    """
    Configure Forge settings.
    """
    config_dir = Path.home() / ".config" / "forge"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.toml"

    config_content = f"""[llm]
provider = "{provider}"
"""

    if api_key:
        config_content += f'api_key = "{api_key}"\n'

    with open(config_file, "w") as f:
        f.write(config_content)

    console.print(f"[green]✓[/green] Configuration saved to {config_file}")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
