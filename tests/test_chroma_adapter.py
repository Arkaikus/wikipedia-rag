"""
Tests for ChromaDB adapter functionality.
"""

import pytest

from src.adapters.chroma_adapter import ChromaAdapter
from src.adapters.vectordb_adapter import CollectionNotFoundError, StorageError
from src.models.schemas import DocumentChunk


class TestChromaAdapter:
    """Test cases for ChromaAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a ChromaAdapter instance."""
        adapter = ChromaAdapter(host="localhost", port=8000)
        return adapter

    @pytest.fixture
    def sample_chunks(self):
        """Create sample document chunks."""
        return [
            DocumentChunk(
                chunk_id="test_001",
                content="Python is a high-level programming language.",
                metadata={"page_title": "Python", "section": "Introduction"},
                source_page_title="Python",
                source_url="https://test.com/python",
                chunk_index=0,
            ),
            DocumentChunk(
                chunk_id="test_002",
                content="It emphasizes code readability and simplicity.",
                metadata={"page_title": "Python", "section": "Philosophy"},
                source_page_title="Python",
                source_url="https://test.com/python",
                chunk_index=1,
            ),
        ]

    @pytest.fixture
    def sample_embeddings(self):
        """Create sample embeddings (random vectors for testing)."""
        import random

        return [[random.random() for _ in range(384)] for _ in range(2)]

    def test_adapter_initialization(self, adapter):
        """Test adapter initializes correctly."""
        assert adapter.host == "localhost"
        assert adapter.port == 8000
        assert adapter.client is None  # Not connected yet

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_initialize_connection(self, adapter):
        """Test connecting to ChromaDB."""
        adapter.initialize()

        assert adapter.client is not None

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_create_collection(self, adapter):
        """Test creating a collection."""
        adapter.initialize()
        collection_name = "test_collection"

        # Clean up if exists
        if adapter.collection_exists(collection_name):
            adapter.delete_collection(collection_name)

        adapter.create_collection(collection_name)

        assert adapter.collection_exists(collection_name)

        # Cleanup
        adapter.delete_collection(collection_name)

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_delete_collection(self, adapter):
        """Test deleting a collection."""
        adapter.initialize()
        collection_name = "test_delete_collection"

        # Create and then delete
        adapter.create_collection(collection_name)
        assert adapter.collection_exists(collection_name)

        adapter.delete_collection(collection_name)
        assert not adapter.collection_exists(collection_name)

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_store_and_retrieve_documents(
        self, adapter, sample_chunks, sample_embeddings
    ):
        """Test storing and retrieving documents."""
        adapter.initialize()
        collection_name = "test_store_collection"

        # Clean up
        if adapter.collection_exists(collection_name):
            adapter.delete_collection(collection_name)

        # Store documents
        adapter.store_documents(collection_name, sample_chunks, sample_embeddings)

        # Verify stored
        info = adapter.get_collection_info(collection_name)
        assert info["count"] == 2

        # Cleanup
        adapter.delete_collection(collection_name)

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_similarity_search(self, adapter, sample_chunks, sample_embeddings):
        """Test similarity search."""
        adapter.initialize()
        collection_name = "test_search_collection"

        # Clean up
        if adapter.collection_exists(collection_name):
            adapter.delete_collection(collection_name)

        # Store documents
        adapter.store_documents(collection_name, sample_chunks, sample_embeddings)

        # Search with first embedding
        results = adapter.similarity_search(
            collection_name, sample_embeddings[0], k=2
        )

        assert len(results) > 0
        assert len(results) <= 2

        # Each result should be (DocumentChunk, score)
        for chunk, score in results:
            assert isinstance(chunk, DocumentChunk)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

        # Cleanup
        adapter.delete_collection(collection_name)

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_search_nonexistent_collection(self, adapter, sample_embeddings):
        """Test searching in non-existent collection raises error."""
        adapter.initialize()

        with pytest.raises(CollectionNotFoundError):
            adapter.similarity_search(
                "nonexistent_collection", sample_embeddings[0], k=5
            )

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_get_collection_info(self, adapter, sample_chunks, sample_embeddings):
        """Test getting collection info."""
        adapter.initialize()
        collection_name = "test_info_collection"

        # Clean up
        if adapter.collection_exists(collection_name):
            adapter.delete_collection(collection_name)

        # Create and store
        adapter.store_documents(collection_name, sample_chunks, sample_embeddings)

        info = adapter.get_collection_info(collection_name)

        assert "name" in info
        assert "count" in info
        assert info["name"] == collection_name
        assert info["count"] == 2

        # Cleanup
        adapter.delete_collection(collection_name)

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_clear_collection(self, adapter, sample_chunks, sample_embeddings):
        """Test clearing a collection."""
        adapter.initialize()
        collection_name = "test_clear_collection"

        # Clean up
        if adapter.collection_exists(collection_name):
            adapter.delete_collection(collection_name)

        # Store documents
        adapter.store_documents(collection_name, sample_chunks, sample_embeddings)
        assert adapter.get_collection_info(collection_name)["count"] == 2

        # Clear
        adapter.clear_collection(collection_name)

        # Verify empty
        info = adapter.get_collection_info(collection_name)
        assert info["count"] == 0

        # Cleanup
        adapter.delete_collection(collection_name)

    def test_get_default_collection_name(self, adapter):
        """Test default collection name generation."""
        name = adapter.get_default_collection_name("Python (programming language)")

        assert name == "wiki_python_programming_language"
        assert " " not in name
        assert "(" not in name
        assert ")" not in name

    # @pytest.mark.skip(reason="Requires Docker/Chroma running")
    def test_batch_storage(self, adapter):
        """Test storing large number of documents in batches."""
        adapter.initialize()
        collection_name = "test_batch_collection"

        # Clean up
        if adapter.collection_exists(collection_name):
            adapter.delete_collection(collection_name)

        # Create 150 chunks (more than batch size of 100)
        chunks = [
            DocumentChunk(
                chunk_id=f"test_{i:04d}",
                content=f"Content for chunk {i}",
                metadata={"index": str(i)},
                source_page_title="Test",
                source_url="https://test.com",
                chunk_index=i,
            )
            for i in range(150)
        ]

        # Create random embeddings
        import random

        embeddings = [[random.random() for _ in range(384)] for _ in range(150)]

        # Store
        adapter.store_documents(collection_name, chunks, embeddings)

        # Verify all stored
        info = adapter.get_collection_info(collection_name)
        assert info["count"] == 150

        # Cleanup
        adapter.delete_collection(collection_name)
