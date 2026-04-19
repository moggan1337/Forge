"""
LLM configuration for Forge.

Defines configuration options for LLM-assisted translation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    NONE = "none"


@dataclass
class LLMConfig:
    """
    Configuration for LLM-assisted translation.

    Attributes:
        provider: The LLM provider to use
        model: The model name to use
        api_key: API key for the provider (optional for some)
        base_url: Base URL for API endpoint
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries on failure
        context_window: Context window size in tokens
        enabled: Whether LLM assistance is enabled
    """

    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.3  # Lower temp for more consistent translations
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
    context_window: int = 128000
    enabled: bool = True

    # Translation-specific options
    preserve_comments: bool = True
    preserve_formatting: bool = True
    idiomatic_output: bool = True  # Prefer idiomatic target language code
    add_type_annotations: bool = True
    explain_translation: bool = False  # Include explanation comments

    # System prompt customization
    system_prompt: str = """You are an expert programmer specializing in code translation.
Your task is to translate code from one programming language to another while:

1. Preserving the exact semantics and behavior of the original code
2. Using idiomatic patterns and conventions of the target language
3. Maintaining code style and formatting similar to common practices in the target language
4. Adding appropriate type annotations where applicable
5. Preserving comments that explain non-obvious logic
6. Converting error handling patterns appropriately (e.g., Rust Result/Option to Go error handling)
7. Converting async/await patterns appropriately
8. Handling language-specific features appropriately

Do NOT:
- Add unnecessary comments or explanations in the output
- Change the logic or behavior of the code
- Use deprecated or non-idiomatic patterns in the target language
- Leave TODO comments unless they were in the original code

Output ONLY the translated code, no explanations."""

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create config from environment variables."""
        import os

        config = cls()

        # Check for API keys
        if api_key := os.environ.get("OPENAI_API_KEY"):
            config.api_key = api_key
            config.provider = LLMProvider.OPENAI

        if api_key := os.environ.get("ANTHROPIC_API_KEY"):
            config.api_key = api_key
            config.provider = LLMProvider.ANTHROPIC

        # Check for model override
        if model := os.environ.get("FORGE_LLM_MODEL"):
            config.model = model

        # Check for base URL override (for proxies/custom endpoints)
        if base_url := os.environ.get("FORGE_LLM_BASE_URL"):
            config.base_url = base_url

        return config

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "enabled": self.enabled,
            "preserve_comments": self.preserve_comments,
            "preserve_formatting": self.preserve_formatting,
            "idiomatic_output": self.idiomatic_output,
            "add_type_annotations": self.add_type_annotations,
        }


@dataclass
class TranslationContext:
    """
    Context information for a translation task.

    Provides additional information to the LLM for better translations.
    """

    source_language: str
    target_language: str
    source_file_path: Optional[str] = None
    target_file_path: Optional[str] = None
    project_type: Optional[str] = None  # e.g., "web", "cli", "library"
    dependencies: list[str] = field(default_factory=list)
    custom_types: dict[str, str] = field(default_factory=dict)  # Type aliases
    conventions: dict[str, str] = field(default_factory=dict)  # Naming conventions
    includes: list[str] = field(default_factory=list)  # Import/include statements

    def to_prompt_context(self) -> str:
        """Generate a string representation for inclusion in prompts."""
        parts = [f"Source language: {self.source_language}"]
        parts.append(f"Target language: {self.target_language}")

        if self.project_type:
            parts.append(f"Project type: {self.project_type}")

        if self.dependencies:
            parts.append(f"Dependencies: {', '.join(self.dependencies)}")

        if self.custom_types:
            type_strs = [f"{k} -> {v}" for k, v in self.custom_types.items()]
            parts.append(f"Custom type mappings: {', '.join(type_strs)}")

        if self.includes:
            parts.append(f"Includes: {', '.join(self.includes)}")

        return "\n".join(parts)
