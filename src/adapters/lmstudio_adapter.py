"""
LMStudio adapter implementation using OpenAI-compatible API.

LMStudio provides a local OpenAI-compatible API server for running LLMs.
"""

from typing import Optional

from openai import OpenAI

from src.adapters.llm_adapter import (
    LLMAdapter,
    LLMConnectionError,
    LLMGenerationError,
    LLMModelNotFoundError,
)
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LMStudioAdapter(LLMAdapter):
    """
    LMStudio implementation of the LLMAdapter.

    Uses OpenAI's Python client to communicate with LMStudio's
    OpenAI-compatible API server (typically running on localhost:1234).

    Note: Automatically handles models that don't support 'system' role by
    prepending system prompts to user messages.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: str = "lm-studio",  # LMStudio doesn't require a real key
    ):
        """
        Initialize LMStudio adapter.

        Args:
            base_url: LMStudio API base URL (default: from settings)
            model: Model name (default: from settings)
            api_key: API key (LMStudio accepts any value)
        """
        settings = get_settings()
        self.base_url = base_url or settings.lmstudio_base_url
        self.model = model or settings.lmstudio_model
        self.api_key = api_key

        # Initialize OpenAI client pointed at LMStudio
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        logger.info(f"LMStudio adapter initialized (base_url={self.base_url})")

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
            system_prompt: Optional system prompt (will be prepended to user message)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        # Build messages
        # Note: Some models don't support "system" role, so we prepend system prompt to user message
        if system_prompt:
            combined_prompt = f"{system_prompt}\n\n{prompt}"
            messages = [{"role": "user", "content": combined_prompt}]
        else:
            messages = [{"role": "user", "content": prompt}]

        return self.chat(messages, temperature=temperature, max_tokens=max_tokens, **kwargs)

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
            **kwargs: Additional parameters

        Returns:
            Generated response text
        """
        try:
            logger.debug(f"Generating response with {len(messages)} messages and model {self.model}")

            # Handle models that don't support "system" role
            # Convert system messages to be prepended to the first user message
            processed_messages = self._process_messages_for_compatibility(messages)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=processed_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Extract the generated text
            generated_text = response.choices[0].message.content

            logger.debug(f"Generated response: {len(generated_text)} characters")

            return generated_text

        except Exception as e:
            logger.error(f"Failed to generate response: {e}", exc_info=True)

            # Categorize the error
            error_msg = str(e).lower()
            if "connection" in error_msg or "refused" in error_msg:
                raise LLMConnectionError(
                    f"Cannot connect to LMStudio at {self.base_url}. "
                    "Make sure LMStudio server is running."
                ) from e
            elif "model" in error_msg and "not found" in error_msg:
                raise LLMModelNotFoundError(
                    f"Model '{self.model}' not found. "
                    "Make sure the model is loaded in LMStudio."
                ) from e
            else:
                raise LLMGenerationError(f"Failed to generate response: {e}") from e

    def get_model_info(self) -> dict:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        try:
            # Try to get available models
            models = self.client.models.list()

            # Find our model
            model_info = None
            for model in models.data:
                if model.id == self.model or self.model in model.id:
                    model_info = {
                        "id": model.id,
                        "created": getattr(model, "created", None),
                        "owned_by": getattr(model, "owned_by", "lmstudio"),
                    }
                    break

            if not model_info:
                # Model not found, return basic info
                model_info = {
                    "id": self.model,
                    "owned_by": "lmstudio",
                    "status": "unknown",
                }

            return model_info

        except Exception as e:
            logger.warning(f"Could not fetch model info: {e}")
            return {
                "id": self.model,
                "owned_by": "lmstudio",
                "error": str(e),
            }

    def is_available(self) -> bool:
        """
        Check if LMStudio service is available.

        Returns:
            True if service is reachable, False otherwise
        """
        try:
            # Try to list models as a health check
            self.client.models.list()
            return True

        except Exception as e:
            logger.debug(f"LMStudio not available: {e}")
            return False

    def _process_messages_for_compatibility(
        self, messages: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """
        Process messages to ensure compatibility with models that don't support system role.

        Some LMStudio models only support 'user' and 'assistant' roles. This method
        converts any 'system' role messages by prepending them to the first 'user' message.

        Args:
            messages: Original messages list

        Returns:
            Processed messages list with only 'user' and 'assistant' roles
        """
        if not messages:
            return messages

        processed = []
        system_content = []

        # Collect all system messages
        for msg in messages:
            if msg.get("role") == "system":
                system_content.append(msg["content"])
            else:
                processed.append(msg)

        # If we have system messages and user messages, prepend system to first user message
        if system_content and processed:
            # Find first user message
            for i, msg in enumerate(processed):
                if msg.get("role") == "user":
                    # Prepend system content
                    system_text = "\n\n".join(system_content)
                    processed[i] = {
                        "role": "user",
                        "content": f"{system_text}\n\n{msg['content']}",
                    }
                    break
        elif system_content and not processed:
            # Only system messages, convert to user message
            processed = [{"role": "user", "content": "\n\n".join(system_content)}]

        return processed

    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate response using query and retrieved context.

        This is a convenience method for RAG that formats the context
        into the prompt.

        Args:
            query: User query
            context: Retrieved context from vector search
            system_prompt: Optional system instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response
        """
        # Default RAG system prompt if none provided
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Use the context to answer the question accurately. "
                "If you use information from the context, cite the source. "
                "If the context doesn't contain relevant information, say so."
            )

        # Format the prompt with context
        prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def get_lmstudio_adapter() -> LMStudioAdapter:
    """
    Get a configured LMStudio adapter instance.

    Returns:
        Initialized LMStudioAdapter
    """
    adapter = LMStudioAdapter()

    # Check if available
    if not adapter.is_available():
        logger.warning(
            "LMStudio server not available. Make sure it's running on "
            f"{adapter.base_url} with a model loaded."
        )

    return adapter
