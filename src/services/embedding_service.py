"""
Embedding service for generating vector embeddings from text.

Uses sentence-transformers for local embedding generation.
"""

from typing import Optional

from sentence_transformers import SentenceTransformer

from src.models.schemas import DocumentChunk, EmbeddingConfig
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings from text using sentence-transformers.

    Supports batch processing and different embedding models.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize the embedding service.

        Args:
            config: Embedding configuration (default: from settings)
        """
        if config is None:
            settings = get_settings()
            config = EmbeddingConfig(
                model_name=settings.embedding_model,
                device=settings.embedding_device,
                batch_size=32,
                normalize_embeddings=True,
            )

        self.config = config
        self.model: Optional[SentenceTransformer] = None
        self.embedding_dimension: Optional[int] = None

        logger.info(
            f"Embedding service initialized with model: {self.config.model_name}, "
            f"device: {self.config.device}"
        )

    def load_model(self) -> None:
        """Load the sentence-transformer model."""
        if self.model is not None:
            logger.debug("Model already loaded")
            return

        try:
            logger.info(f"Loading embedding model: {self.config.model_name}")

            self.model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device,
            )

            # Get embedding dimension
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()

            logger.info(
                f"Model loaded successfully. Embedding dimension: {self.embedding_dimension}"
            )

        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load embedding model: {e}") from e

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.model is None:
            self.load_model()

        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=self.config.normalize_embeddings,
                convert_to_numpy=True,
            )

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}") from e

    def embed_texts(self, texts: list[str], show_progress: bool = True) -> list[list[float]]:
        """
        Generate embeddings for multiple texts (batch processing).

        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        if self.model is None:
            self.load_model()

        if not texts:
            logger.warning("No texts provided for embedding")
            return []

        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")

            embeddings = self.model.encode(
                texts,
                batch_size=self.config.batch_size,
                normalize_embeddings=self.config.normalize_embeddings,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )

            # Convert to list of lists
            embeddings_list = embeddings.tolist()

            logger.info(f"Generated {len(embeddings_list)} embeddings")

            return embeddings_list

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e

    def embed_chunks(
        self, chunks: list[DocumentChunk], show_progress: bool = True
    ) -> list[list[float]]:
        """
        Generate embeddings for document chunks.

        Args:
            chunks: List of DocumentChunk objects
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors matching chunk order
        """
        texts = [chunk.content for chunk in chunks]
        return self.embed_texts(texts, show_progress=show_progress)

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.

        Returns:
            Embedding dimension
        """
        if self.embedding_dimension is None:
            if self.model is None:
                self.load_model()

        return self.embedding_dimension or 0


# Global instance cache
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(config: Optional[EmbeddingConfig] = None) -> EmbeddingService:
    """
    Get or create the global embedding service instance.

    Args:
        config: Optional embedding configuration

    Returns:
        EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService(config=config)
        _embedding_service.load_model()

    return _embedding_service


def reset_embedding_service() -> None:
    """Reset the global embedding service instance (useful for testing)."""
    global _embedding_service
    _embedding_service = None
