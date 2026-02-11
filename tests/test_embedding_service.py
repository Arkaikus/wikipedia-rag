"""
Tests for embedding service functionality.
"""

import pytest

from src.models.schemas import DocumentChunk, EmbeddingConfig
from src.services.embedding_service import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """Test cases for EmbeddingService."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        config = EmbeddingConfig(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
            batch_size=32,
        )
        service = EmbeddingService(config=config)

        assert service.config.model_name == "all-MiniLM-L6-v2"
        assert service.config.device == "cpu"
        assert service.model is None  # Not loaded yet

    def test_load_model(self):
        """Test model loading."""
        service = EmbeddingService()
        service.load_model()

        assert service.model is not None
        assert service.embedding_dimension is not None
        assert service.embedding_dimension > 0

    def test_embed_single_text(self):
        """Test embedding a single text."""
        service = EmbeddingService()
        text = "This is a test sentence."

        embedding = service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        service = EmbeddingService()
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence.",
        ]

        embeddings = service.embed_texts(texts, show_progress=False)

        assert len(embeddings) == 3
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) == len(embeddings[0]) for emb in embeddings)

    def test_embed_empty_list(self):
        """Test embedding empty list returns empty."""
        service = EmbeddingService()

        embeddings = service.embed_texts([], show_progress=False)

        assert embeddings == []

    def test_embed_chunks(self):
        """Test embedding document chunks."""
        service = EmbeddingService()

        chunks = [
            DocumentChunk(
                chunk_id="test_1",
                content="First chunk content.",
                metadata={},
                source_page_title="Test",
                source_url="http://test.com",
                chunk_index=0,
            ),
            DocumentChunk(
                chunk_id="test_2",
                content="Second chunk content.",
                metadata={},
                source_page_title="Test",
                source_url="http://test.com",
                chunk_index=1,
            ),
        ]

        embeddings = service.embed_chunks(chunks, show_progress=False)

        assert len(embeddings) == 2
        assert all(isinstance(emb, list) for emb in embeddings)

    def test_embedding_dimension(self):
        """Test getting embedding dimension."""
        service = EmbeddingService()
        service.load_model()

        dimension = service.get_embedding_dimension()

        assert dimension > 0
        # all-MiniLM-L6-v2 has 384 dimensions
        assert dimension == 384

    def test_embeddings_are_normalized(self):
        """Test that embeddings are normalized when configured."""
        config = EmbeddingConfig(normalize_embeddings=True)
        service = EmbeddingService(config=config)

        embedding = service.embed_text("Test sentence")

        # Check if roughly unit length (normalized)
        import math

        magnitude = math.sqrt(sum(x**2 for x in embedding))
        assert 0.99 <= magnitude <= 1.01  # Allow small floating point error

    def test_similar_texts_have_similar_embeddings(self):
        """Test that similar texts produce similar embeddings."""
        service = EmbeddingService()

        text1 = "The cat sits on the mat"
        text2 = "A cat is sitting on a mat"
        text3 = "Python is a programming language"

        emb1 = service.embed_text(text1)
        emb2 = service.embed_text(text2)
        emb3 = service.embed_text(text3)

        # Compute cosine similarity
        def cosine_similarity(a: list[float], b: list[float]) -> float:
            import math

            dot_product = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x**2 for x in a))
            mag_b = math.sqrt(sum(y**2 for y in b))
            return dot_product / (mag_a * mag_b)

        sim_1_2 = cosine_similarity(emb1, emb2)
        sim_1_3 = cosine_similarity(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_1_2 > sim_1_3
        assert sim_1_2 > 0.7  # High similarity threshold

    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns singleton."""
        service1 = get_embedding_service()
        service2 = get_embedding_service()

        assert service1 is service2  # Same instance
