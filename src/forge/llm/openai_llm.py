"""
OpenAI API client for Forge.

Provides integration with OpenAI's API for LLM-assisted translation.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Optional

try:
    from openai import AsyncOpenAI, OpenAIError

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from forge.llm.llm_config import LLMConfig, LLMProvider


class OpenAIClient:
    """
    Client for OpenAI API integration.

    Handles authentication, request formatting, and response parsing
    for OpenAI's language models.
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize the OpenAI client.

        Args:
            config: LLM configuration
        """
        self.config = config
        self._client: Optional[Any] = None

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )

        # Get API key
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or provide api_key in config."
            )

        # Initialize client
        init_kwargs: dict[str, Any] = {"api_key": api_key}
        if config.base_url:
            init_kwargs["base_url"] = config.base_url

        self._client = AsyncOpenAI(**init_kwargs)

    @property
    def provider(self) -> LLMProvider:
        """Get the provider type."""
        return LLMProvider.OPENAI

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

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )

            return response.choices[0].message.content or ""

        except OpenAIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e
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

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}") from e

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the model's tokenizer.

        Note: This is an approximation using simple word counting.
        For accurate counts, use tiktoken or the OpenAI tokenizer API.

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


class LLMError(Exception):
    """Exception raised for LLM-related errors."""

    pass
