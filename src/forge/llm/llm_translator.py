"""
LLM-powered translation engine for Forge.

Provides intelligent, context-aware code translation using LLMs.
"""

from __future__ import annotations

import re
from typing import Optional

from forge.llm.llm_config import LLMConfig, TranslationContext
from forge.llm.openai_llm import OpenAIClient, LLMError
from forge.llm.anthropic_llm import AnthropicClient


class LLMTranslator:
    """
    LLM-powered code translator.

    Uses large language models to translate code with awareness of
    idioms, conventions, and best practices in both source and target languages.
    """

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        """
        Initialize the LLM translator.

        Args:
            config: LLM configuration, uses defaults if not provided
        """
        self.config = config or LLMConfig()
        self._client = self._create_client()

    def _create_client(self) -> Optional[OpenAIClient | AnthropicClient]:
        """Create the appropriate LLM client based on configuration."""
        if not self.config.enabled:
            return None

        if self.config.provider.value == "openai":
            return OpenAIClient(self.config)
        elif self.config.provider.value == "anthropic":
            return AnthropicClient(self.config)
        else:
            return None

    async def translate(
        self,
        source_code: str,
        source_lang: str,
        target_lang: str,
        context: Optional[TranslationContext] = None,
    ) -> str:
        """
        Translate code from source language to target language.

        Args:
            source_code: The source code to translate
            source_lang: Source language name
            target_lang: Target language name
            context: Optional translation context

        Returns:
            Translated code in the target language
        """
        if not self._client:
            raise LLMError("LLM client not configured. Set api_key or use config.enabled=False.")

        # Build the prompt
        prompt = self._build_translation_prompt(source_code, source_lang, target_lang, context)

        # Get completion
        try:
            result = await self._client.complete(
                prompt=prompt,
                system_prompt=self.config.system_prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            # Extract code from result (remove markdown code blocks if present)
            return self._extract_code(result, target_lang)

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Translation failed: {e}") from e

    async def translate_stream(
        self,
        source_code: str,
        source_lang: str,
        target_lang: str,
        context: Optional[TranslationContext] = None,
    ):
        """
        Translate code with streaming output.

        Args:
            source_code: The source code to translate
            source_lang: Source language name
            target_lang: Target language name
            context: Optional translation context

        Yields:
            Chunks of translated code
        """
        if not self._client:
            raise LLMError("LLM client not configured.")

        prompt = self._build_translation_prompt(source_code, source_lang, target_lang, context)

        try:
            async for chunk in self._client.complete_stream(
                prompt=prompt,
                system_prompt=self.config.system_prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            ):
                yield chunk

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Streaming translation failed: {e}") from e

    def _build_translation_prompt(
        self,
        source_code: str,
        source_lang: str,
        target_lang: str,
        context: Optional[TranslationContext] = None,
    ) -> str:
        """Build the translation prompt with context."""
        prompt_parts = [f"Translate the following {source_lang} code to {target_lang}:\n"]
        prompt_parts.append("```" + source_lang)
        prompt_parts.append(source_code)
        prompt_parts.append("```")

        if context:
            prompt_parts.append("\nContext:")
            prompt_parts.append(context.to_prompt_context())

        # Add specific instructions based on target language
        if target_lang.lower() == "python":
            prompt_parts.append("\nFor Python output:")
            prompt_parts.append("- Use snake_case for function and variable names")
            prompt_parts.append("- Use type hints from the typing module")
            prompt_parts.append("- Convert classes to Python classes with __init__ methods")
            prompt_parts.append("- Handle null/undefined as None")
            prompt_parts.append("- Use list/dict comprehensions where appropriate")

        elif target_lang.lower() == "typescript":
            prompt_parts.append("\nFor TypeScript output:")
            prompt_parts.append("- Use camelCase for function and variable names")
            prompt_parts.append("- Add appropriate TypeScript types/interfaces")
            prompt_parts.append("- Convert classes to TypeScript classes with proper typing")
            prompt_parts.append("- Use async/await for asynchronous operations")

        elif target_lang.lower() == "rust":
            prompt_parts.append("\nFor Rust output:")
            prompt_parts.append("- Use snake_case for function and variable names")
            prompt_parts.append("- Use proper Rust types (Option, Result, Vec, etc.)")
            prompt_parts.append("- Handle ownership and borrowing appropriately")
            prompt_parts.append("- Use match expressions for pattern matching")
            prompt_parts.append("- Add appropriate lifetime annotations if needed")

        elif target_lang.lower() == "go":
            prompt_parts.append("\nFor Go output:")
            prompt_parts.append("- Use PascalCase for exported names, camelCase for unexported")
            prompt_parts.append("- Use proper Go error handling with error return values")
            prompt_parts.append("- Use goroutines and channels where appropriate")
            prompt_parts.append("- Follow Go idioms and conventions")

        prompt_parts.append("\n```" + target_lang)
        prompt_parts.append("[YOUR TRANSLATED CODE HERE]")
        prompt_parts.append("```")

        return "\n".join(prompt_parts)

    def _extract_code(self, text: str, target_lang: str) -> str:
        """Extract code from LLM response, removing markdown formatting."""
        # Try to find code block
        code_block_pattern = rf"```(?:{target_lang})?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)

        if matches:
            # Return the largest match (likely the full code)
            return max(matches, key=len).strip()

        # Fallback: try generic code block
        generic_pattern = r"```\s*([\s\S]*?)```"
        generic_matches = re.findall(generic_pattern, text)

        if generic_matches:
            return max(generic_matches, key=len).strip()

        # Last resort: return as-is
        return text.strip()

    async def close(self) -> None:
        """Close the LLM client."""
        if self._client:
            await self._client.close()
            self._client = None


class BatchLLMTranslator:
    """
    Batch translator for multiple files or large codebases.

    Handles batching, rate limiting, and context preservation
    across multiple translation requests.
    """

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        """
        Initialize the batch translator.

        Args:
            config: LLM configuration
        """
        self.config = config or LLMConfig()
        self._translator = LLMTranslator(self.config)

    async def translate_batch(
        self,
        files: list[tuple[str, str, str]],  # [(code, source_lang, target_lang), ...]
        context: Optional[TranslationContext] = None,
    ) -> list[str]:
        """
        Translate a batch of files.

        Args:
            files: List of (code, source_lang, target_lang) tuples
            context: Optional shared context

        Returns:
            List of translated code strings
        """
        results = []

        for code, source_lang, target_lang in files:
            result = await self._translator.translate(
                source_code=code,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
            )
            results.append(result)

        return results

    async def translate_file(
        self,
        source_file: str,
        target_file: str,
        source_lang: str,
        target_lang: str,
    ) -> str:
        """
        Translate a file.

        Args:
            source_file: Path to source file
            target_file: Path to write translated file
            source_lang: Source language
            target_lang: Target language

        Returns:
            Translated code
        """
        # Read source file
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Translate
        result = await self._translator.translate(
            source_code=source_code,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        # Write target file
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(result)

        return result

    async def close(self) -> None:
        """Close resources."""
        await self._translator.close()
