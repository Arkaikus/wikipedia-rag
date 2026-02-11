"""
Abstract adapter interface for vector databases.

Provides a unified interface for different vector database implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.models.schemas import DocumentChunk


class VectorDBAdapter(ABC):
    """
    Abstract base class for vector database adapters.

    Implements the adapter pattern to allow seamless switching between
    different vector database implementations (Chroma, Weaviate, Pinecone, etc.).
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the vector database connection."""
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, **kwargs) -> None:
        """
        Create a new collection/index in the vector database.

        Args:
            collection_name: Name of the collection to create
            **kwargs: Additional database-specific parameters
        """
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection/index from the vector database.

        Args:
            collection_name: Name of the collection to delete
        """
        pass

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if collection exists, False otherwise
        """
        pass

    @abstractmethod
    def store_documents(
        self,
        collection_name: str,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Store document chunks with their embeddings in the database.

        Args:
            collection_name: Name of the collection to store in
            chunks: List of DocumentChunk objects
            embeddings: List of embedding vectors (must match chunks length)
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        collection_name: str,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for similar documents based on query embedding.

        Args:
            collection_name: Name of the collection to search in
            query_embedding: Query vector
            k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of tuples (DocumentChunk, similarity_score)
        """
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        """
        Get information about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection metadata (count, dimensions, etc.)
        """
        pass

    @abstractmethod
    def clear_collection(self, collection_name: str) -> None:
        """
        Clear all documents from a collection without deleting it.

        Args:
            collection_name: Name of the collection to clear
        """
        pass

    def get_default_collection_name(self, page_title: str) -> str:
        """
        Generate a default collection name from page title.

        Args:
            page_title: Wikipedia page title

        Returns:
            Sanitized collection name
        """
        # Sanitize collection name (lowercase, replace spaces with underscores)
        sanitized = page_title.lower().replace(" ", "_")
        # Remove special characters
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        # Prefix to identify as wikipedia
        return f"wiki_{sanitized}"


class VectorDBError(Exception):
    """Base exception for vector database errors."""

    pass


class CollectionNotFoundError(VectorDBError):
    """Raised when a collection doesn't exist."""

    pass


class StorageError(VectorDBError):
    """Raised when storing documents fails."""

    pass


class SearchError(VectorDBError):
    """Raised when search operation fails."""

    pass
