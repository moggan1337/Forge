"""
Anthropic API client for Forge.

Provides integration with Anthropic's Claude API for LLM-assisted translation.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Optional

try:
    from anthropic import AsyncAnthropic, AnthropicError

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from forge.llm.llm_config import LLMConfig, LLMProvider
from forge.llm.openai_llm import LLMError


class AnthropicClient:
    """
    Client for Anthropic API integration.

    Handles authentication, request formatting, and response parsing
    for Anthropic's Claude models.
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize the Anthropic client.

        Args:
            config: LLM configuration
        """
        self.config = config
        self._client: Optional[Any] = None

        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        # Get API key
        api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or provide api_key in config."
            )

        # Initialize client
        init_kwargs: dict[str, Any] = {"api_key": api_key}
        if config.base_url:
            init_kwargs["base_url"] = config.base_url

        self._client = AsyncAnthropic(**init_kwargs)

        # Map model names
        self._model_mapping = {
            "claude-opus-4": "claude-opus-4-20240229",
            "claude-sonnet-4": "claude-sonnet-4-20240229",
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307",
        }

    @property
    def provider(self) -> LLMProvider:
        """Get the provider type."""
        return LLMProvider.ANTHROPIC

    def _get_model_name(self) -> str:
        """Get the actual model name for API calls."""
        return self._model_mapping.get(self.config.model, self.config.model)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion from the model.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            The generated text completion
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        try:
            response = await self._client.messages.create(
                model=self._get_model_name(),
                max_tokens=max_tokens or min(self.config.max_tokens, 4096),
                temperature=temperature or self.config.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text if response.content else ""

        except AnthropicError as e:
            raise LLMError(f"Anthropic API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}") from e

    async def complete_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming completion from the model.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Yields:
            Chunks of generated text
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        try:
            async with self._client.messages.stream(
                model=self._get_model_name(),
                max_tokens=max_tokens or min(self.config.max_tokens, 4096),
                temperature=temperature or self.config.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except AnthropicError as e:
            raise LLMError(f"Anthropic API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}") from e

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Note: This is an approximation. For accurate counts, use Anthropic's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Simple approximation: ~4 characters per token
        return len(text) // 4 + 1

    async def close(self) -> None:
        """Close the client and clean up resources."""
        if self._client:
            await self._client.close()
            self._client = None
