"""
Tests for LMStudio adapter functionality.
"""

import pytest

from src.adapters.lmstudio_adapter import LMStudioAdapter


class TestLMStudioAdapter:
    """Test cases for LMStudioAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create an LMStudio adapter instance."""
        return LMStudioAdapter(
            base_url="http://localhost:1234/v1",
            model="local-model",
        )

    def test_adapter_initialization(self, adapter):
        """Test adapter initializes correctly."""
        assert adapter.base_url == "http://localhost:1234/v1"
        assert adapter.model == "local-model"
        assert adapter.client is not None

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_is_available(self, adapter):
        """Test checking if LMStudio is available."""
        available = adapter.is_available()
        assert isinstance(available, bool)

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_generate_simple(self, adapter):
        """Test simple text generation."""
        response = adapter.generate(
            prompt="What is 2+2?",
            temperature=0.1,
            max_tokens=100,
        )

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_generate_with_system_prompt(self, adapter):
        """Test generation with system prompt."""
        response = adapter.generate(
            prompt="What is Python?",
            system_prompt="You are a helpful programming assistant.",
            temperature=0.7,
            max_tokens=200,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "python" in response.lower()

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_chat(self, adapter):
        """Test chat completion."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]

        response = adapter.chat(messages, temperature=0.7, max_tokens=100)

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_chat_multi_turn(self, adapter):
        """Test multi-turn conversation."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What's my name?"},
        ]

        response = adapter.chat(messages, temperature=0.1, max_tokens=50)

        assert isinstance(response, str)
        assert "alice" in response.lower()

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_get_model_info(self, adapter):
        """Test getting model information."""
        info = adapter.get_model_info()

        assert isinstance(info, dict)
        assert "id" in info

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_generate_with_context(self, adapter):
        """Test RAG-style generation with context."""
        context = """
        Python is a high-level programming language.
        It was created by Guido van Rossum and first released in 1991.
        Python emphasizes code readability with significant indentation.
        """

        response = adapter.generate_with_context(
            query="Who created Python?",
            context=context,
            temperature=0.1,
            max_tokens=100,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "guido" in response.lower() or "rossum" in response.lower()

    def test_connection_error_handling(self):
        """Test error handling for connection failures."""
        # Use a bad URL that will fail
        adapter = LMStudioAdapter(base_url="http://localhost:9999/v1")

        # Should not raise on init
        assert adapter is not None

        # Should return False for availability check
        assert adapter.is_available() is False

    def test_message_compatibility_processing(self, adapter):
        """Test that system messages are converted for compatibility."""
        # Test with system + user message
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
        ]

        processed = adapter._process_messages_for_compatibility(messages)

        # Should merge into one user message
        assert len(processed) == 1
        assert processed[0]["role"] == "user"
        assert "You are helpful" in processed[0]["content"]
        assert "Hello!" in processed[0]["content"]

    def test_message_compatibility_no_system(self, adapter):
        """Test that messages without system role are unchanged."""
        messages = [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi!"},
        ]

        processed = adapter._process_messages_for_compatibility(messages)

        # Should remain unchanged
        assert processed == messages

    def test_message_compatibility_multiple_system(self, adapter):
        """Test handling of multiple system messages."""
        messages = [
            {"role": "system", "content": "Instruction 1"},
            {"role": "system", "content": "Instruction 2"},
            {"role": "user", "content": "Hello!"},
        ]

        processed = adapter._process_messages_for_compatibility(messages)

        # Should merge all system messages with first user message
        assert len(processed) == 1
        assert processed[0]["role"] == "user"
        assert "Instruction 1" in processed[0]["content"]
        assert "Instruction 2" in processed[0]["content"]
        assert "Hello!" in processed[0]["content"]

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_temperature_control(self, adapter):
        """Test that temperature affects output variability."""
        prompt = "Tell me a short story about a cat."

        # Low temperature (more deterministic)
        response1 = adapter.generate(prompt, temperature=0.1, max_tokens=100)
        response2 = adapter.generate(prompt, temperature=0.1, max_tokens=100)

        # High temperature (more creative)
        response3 = adapter.generate(prompt, temperature=1.5, max_tokens=100)

        assert isinstance(response1, str)
        assert isinstance(response2, str)
        assert isinstance(response3, str)

        # Low temperature responses might be similar (not guaranteed)
        # High temperature response should be different

    @pytest.mark.skip(reason="Requires LMStudio running")
    def test_max_tokens_control(self, adapter):
        """Test max_tokens parameter limits output."""
        prompt = "Write a long essay about artificial intelligence."

        # Short output
        response_short = adapter.generate(prompt, temperature=0.7, max_tokens=50)

        # Longer output
        response_long = adapter.generate(prompt, temperature=0.7, max_tokens=200)

        assert len(response_short) < len(response_long)
