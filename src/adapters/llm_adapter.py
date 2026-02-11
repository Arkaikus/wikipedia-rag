"""
Abstract adapter interface for Large Language Models.

Provides a unified interface for different LLM implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional


class LLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.

    Implements the adapter pattern to allow seamless switching between
    different LLM providers (LMStudio, OpenAI, Azure, Anthropic, etc.).
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: The user prompt/query
            system_prompt: Optional system prompt for instructions
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> str:
        """
        Generate chat completion from conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated response text
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information (name, context_length, etc.)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if service is reachable, False otherwise
        """
        pass


class LLMError(Exception):
    """Base exception for LLM errors."""

    pass


class LLMConnectionError(LLMError):
    """Raised when cannot connect to LLM service."""

    pass


class LLMGenerationError(LLMError):
    """Raised when text generation fails."""

    pass


class LLMModelNotFoundError(LLMError):
    """Raised when specified model is not available."""

    pass
