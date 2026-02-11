"""
ChromaDB adapter implementation.

Implements the VectorDBAdapter interface for ChromaDB.
"""

from typing import Optional

import chromadb
from chromadb.config import Settings

from src.adapters.vectordb_adapter import (
    CollectionNotFoundError,
    SearchError,
    StorageError,
    VectorDBAdapter,
)
from src.models.schemas import DocumentChunk
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaAdapter(VectorDBAdapter):
    """
    ChromaDB implementation of the VectorDBAdapter.

    Provides persistent storage and similarity search using ChromaDB.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize ChromaDB adapter.

        Args:
            host: ChromaDB host (default: from settings)
            port: ChromaDB port (default: from settings)
        """
        settings = get_settings()
        self.host = host or settings.chroma_host
        self.port = port or settings.chroma_port
        self.client: Optional[chromadb.HttpClient] = None
        self.collections: dict = {}

        logger.info(f"ChromaDB adapter initialized (host={self.host}, port={self.port})")

    def initialize(self) -> None:
        """Initialize connection to ChromaDB."""
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(anonymized_telemetry=False),
            )

            # Test connection
            self.client.heartbeat()

            logger.info("ChromaDB connection established successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}", exc_info=True)
            raise StorageError(f"Failed to connect to ChromaDB: {e}") from e

    def create_collection(self, collection_name: str, **kwargs) -> None:
        """
        Create a new collection in ChromaDB.

        Args:
            collection_name: Name of the collection
            **kwargs: Additional parameters (metadata, distance_function, etc.)
        """
        if self.client is None:
            self.initialize()

        try:
            # Check if collection already exists
            if self.collection_exists(collection_name):
                logger.warning(f"Collection '{collection_name}' already exists")
                return

            # Create collection with metadata
            metadata = kwargs.get("metadata", {})
            metadata["created_by"] = "rag-chatbot"

            collection = self.client.create_collection(
                name=collection_name,
                metadata=metadata,
            )

            self.collections[collection_name] = collection

            logger.info(f"Created collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}", exc_info=True)
            raise StorageError(f"Failed to create collection: {e}") from e

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection from ChromaDB.

        Args:
            collection_name: Name of the collection to delete
        """
        if self.client is None:
            self.initialize()

        try:
            self.client.delete_collection(name=collection_name)

            # Remove from cache
            if collection_name in self.collections:
                del self.collections[collection_name]

            logger.info(f"Deleted collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}", exc_info=True)
            raise StorageError(f"Failed to delete collection: {e}") from e

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists in ChromaDB.

        Args:
            collection_name: Name of the collection

        Returns:
            True if exists, False otherwise
        """
        if self.client is None:
            self.initialize()

        try:
            collections = self.client.list_collections()
            return any(col.name == collection_name for col in collections)

        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}", exc_info=True)
            return False

    def _get_collection(self, collection_name: str):
        """Get or retrieve a collection."""
        if self.client is None:
            self.initialize()

        # Check cache first
        if collection_name in self.collections:
            return self.collections[collection_name]

        # Get from database
        try:
            collection = self.client.get_collection(name=collection_name)
            self.collections[collection_name] = collection
            return collection

        except Exception as e:
            raise CollectionNotFoundError(
                f"Collection '{collection_name}' not found: {e}"
            ) from e

    def store_documents(
        self,
        collection_name: str,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """
        Store document chunks with embeddings in ChromaDB.

        Args:
            collection_name: Name of the collection
            chunks: List of DocumentChunk objects
            embeddings: List of embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        if not chunks:
            logger.warning("No chunks to store")
            return

        try:
            # Create collection if it doesn't exist
            if not self.collection_exists(collection_name):
                self.create_collection(collection_name)

            collection = self._get_collection(collection_name)

            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]

            # Store in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_end = min(i + batch_size, len(chunks))

                collection.add(
                    ids=ids[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                )

                logger.debug(
                    f"Stored batch {i // batch_size + 1}: "
                    f"{batch_end - i} chunks in '{collection_name}'"
                )

            logger.info(f"Stored {len(chunks)} chunks in collection '{collection_name}'")

        except Exception as e:
            logger.error(f"Failed to store documents: {e}", exc_info=True)
            raise StorageError(f"Failed to store documents: {e}") from e

    def similarity_search(
        self,
        collection_name: str,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Search for similar documents in ChromaDB.

        Args:
            collection_name: Name of the collection
            query_embedding: Query vector
            k: Number of results
            filter_metadata: Optional metadata filters

        Returns:
            List of (DocumentChunk, similarity_score) tuples
        """
        try:
            collection = self._get_collection(collection_name)

            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )

            # Convert results to DocumentChunk objects
            search_results = []

            if results["ids"] and len(results["ids"]) > 0:
                for idx in range(len(results["ids"][0])):
                    chunk_id = results["ids"][0][idx]
                    content = results["documents"][0][idx]
                    metadata = results["metadatas"][0][idx]
                    distance = results["distances"][0][idx]

                    # Convert distance to similarity score (lower distance = higher similarity)
                    # ChromaDB uses L2 distance, convert to similarity [0-1]
                    similarity = 1.0 / (1.0 + distance)

                    # Reconstruct DocumentChunk
                    chunk = DocumentChunk(
                        chunk_id=chunk_id,
                        content=content,
                        metadata=metadata,
                        source_page_title=metadata.get("page_title", ""),
                        source_url=metadata.get("page_url", ""),
                        section_title=metadata.get("section"),
                        chunk_index=int(metadata.get("chunk_index", 0)),
                    )

                    search_results.append((chunk, similarity))

            logger.info(
                f"Found {len(search_results)} results in collection '{collection_name}'"
            )

            return search_results

        except CollectionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise SearchError(f"Search failed: {e}") from e

    def get_collection_info(self, collection_name: str) -> dict:
        """
        Get information about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary with collection info
        """
        try:
            collection = self._get_collection(collection_name)

            count = collection.count()
            metadata = collection.metadata

            return {
                "name": collection_name,
                "count": count,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}", exc_info=True)
            raise StorageError(f"Failed to get collection info: {e}") from e

    def clear_collection(self, collection_name: str) -> None:
        """
        Clear all documents from a collection.

        Args:
            collection_name: Name of the collection
        """
        try:
            # ChromaDB doesn't have a direct clear method
            # So we delete and recreate the collection
            if self.collection_exists(collection_name):
                # Get metadata before deleting
                info = self.get_collection_info(collection_name)
                metadata = info.get("metadata", {})

                # Delete and recreate
                self.delete_collection(collection_name)
                self.create_collection(collection_name, metadata=metadata)

                logger.info(f"Cleared collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to clear collection: {e}", exc_info=True)
            raise StorageError(f"Failed to clear collection: {e}") from e


def get_chroma_adapter() -> ChromaAdapter:
    """
    Get a configured ChromaDB adapter instance.

    Returns:
        Initialized ChromaAdapter
    """
    adapter = ChromaAdapter()
    adapter.initialize()
    return adapter
