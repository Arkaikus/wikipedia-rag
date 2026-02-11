"""
RAG Service - Main orchestration for Retrieval-Augmented Generation.

Coordinates Wikipedia scraping, document processing, embedding generation,
vector storage, similarity search, and LLM response generation.
"""

from typing import Optional

from src.adapters.chroma_adapter import ChromaAdapter
from src.adapters.llm_adapter import LLMAdapter
from src.adapters.lmstudio_adapter import LMStudioAdapter
from src.models.schemas import DocumentChunk, QueryResult
from src.services.document_processor import DocumentProcessor
from src.services.embedding_service import EmbeddingService
from src.services.wikipedia_scraper import WikipediaScraper
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    Main RAG service that coordinates all components.

    Provides high-level methods for loading Wikipedia pages and
    answering questions using retrieval-augmented generation.
    """

    def __init__(
        self,
        llm_adapter: Optional[LLMAdapter] = None,
        vector_db: Optional[ChromaAdapter] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        """
        Initialize RAG service with components.

        Args:
            llm_adapter: LLM adapter (default: LMStudio)
            vector_db: Vector database adapter (default: Chroma)
            embedding_service: Embedding service (default: sentence-transformers)
        """
        self.settings = get_settings()

        # Initialize components
        self.llm = llm_adapter or LMStudioAdapter()
        self.vector_db = vector_db or ChromaAdapter()
        self.embedding_service = embedding_service or EmbeddingService()

        # Initialize other services
        self.scraper = WikipediaScraper()
        self.processor = DocumentProcessor()

        # Current page state
        self.current_page_title: Optional[str] = None
        self.current_collection: Optional[str] = None

        # Connect to services
        self._initialize_services()

        logger.info("RAG service initialized")

    def _initialize_services(self) -> None:
        """Initialize and connect to external services."""
        try:
            # Initialize vector DB
            if not hasattr(self.vector_db, "client") or self.vector_db.client is None:
                self.vector_db.initialize()
                logger.info("Vector database connected")

            # Load embedding model
            if not hasattr(self.embedding_service, "model") or self.embedding_service.model is None:
                self.embedding_service.load_model()
                logger.info("Embedding model loaded")

            # Check LLM availability
            if self.llm.is_available():
                logger.info("LLM service available")
            else:
                logger.warning("LLM service not available - responses will fail")

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise

    def load_wikipedia_page(self, page_identifier: str) -> dict:
        """
        Load and index a Wikipedia page.

        Args:
            page_identifier: Wikipedia page title or URL

        Returns:
            Dictionary with page info and indexing stats
        """
        logger.info(f"Loading Wikipedia page: {page_identifier}")

        try:
            # 1. Fetch Wikipedia page
            page = self.scraper.fetch(page_identifier)
            logger.info(f"Fetched page: {page.title} ({page.word_count:,} words)")

            # 2. Process into chunks
            chunks = self.processor.process_page(page)
            logger.info(f"Processed into {len(chunks)} chunks")

            # 3. Generate embeddings
            embeddings = self.embedding_service.embed_chunks(chunks, show_progress=True)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # 4. Store in vector database
            collection_name = self.vector_db.get_default_collection_name(page.title)

            # Clear existing collection if it exists
            if self.vector_db.collection_exists(collection_name):
                logger.info(f"Clearing existing collection: {collection_name}")
                self.vector_db.delete_collection(collection_name)

            self.vector_db.store_documents(collection_name, chunks, embeddings)
            logger.info(f"Stored in collection: {collection_name}")

            # Update current state
            self.current_page_title = page.title
            self.current_collection = collection_name

            # Get statistics
            stats = self.processor.get_chunk_stats(chunks)
            collection_info = self.vector_db.get_collection_info(collection_name)

            return {
                "title": page.title,
                "url": page.url,
                "word_count": page.word_count,
                "sections": len(page.sections),
                "chunks": len(chunks),
                "collection": collection_name,
                "stats": stats,
                "collection_info": collection_info,
            }

        except Exception as e:
            logger.error(f"Failed to load Wikipedia page: {e}", exc_info=True)
            raise

    def query(
        self,
        question: str,
        k: int = 5,
        min_similarity: float = 0.0,
        include_context: bool = True,
    ) -> QueryResult:
        """
        Answer a question using RAG.

        Args:
            question: User question
            k: Number of chunks to retrieve
            min_similarity: Minimum similarity threshold
            include_context: Whether to include full context in result

        Returns:
            QueryResult with answer and retrieved context
        """
        if not self.current_collection:
            raise ValueError("No Wikipedia page loaded. Call load_wikipedia_page() first.")

        logger.info(f"Processing query: {question}")

        try:
            # 1. Generate query embedding
            query_embedding = self.embedding_service.embed_text(question)
            logger.debug("Generated query embedding")

            # 2. Retrieve relevant chunks
            results = self.vector_db.similarity_search(
                self.current_collection,
                query_embedding,
                k=k,
            )
            logger.info(f"Retrieved {len(results)} chunks")

            # Filter by similarity threshold
            filtered_results = [
                (chunk, score) for chunk, score in results if score >= min_similarity
            ]

            if not filtered_results:
                logger.warning("No results above similarity threshold")
                return QueryResult(
                    query=question,
                    retrieved_chunks=[],
                    similarity_scores=[],
                    context="No relevant context found.",
                    metadata={
                        "page_title": self.current_page_title,
                        "k": k,
                        "min_similarity": min_similarity,
                    },
                )

            # 3. Assemble context
            chunks = [chunk for chunk, _ in filtered_results]
            scores = [score for _, score in filtered_results]

            context = self._assemble_context(chunks)
            logger.debug(f"Assembled context: {len(context)} characters")

            # 4. Generate response with LLM
            response = self.llm.generate_with_context(
                query=question,
                context=context,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
            )
            logger.info("Generated LLM response")

            # 5. Add citations to response
            response_with_citations = self._add_citations(response, chunks)

            # Build result
            query_result = QueryResult(
                query=question,
                retrieved_chunks=chunks if include_context else [],
                similarity_scores=scores,
                context=response_with_citations,
                metadata={
                    "page_title": self.current_page_title,
                    "k": k,
                    "min_similarity": min_similarity,
                    "num_results": len(filtered_results),
                },
            )

            return query_result

        except Exception as e:
            logger.error(f"Failed to process query: {e}", exc_info=True)
            raise

    def _assemble_context(self, chunks: list[DocumentChunk]) -> str:
        """
        Assemble context from retrieved chunks.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            Formatted context string
        """
        context_parts = []

        for idx, chunk in enumerate(chunks, 1):
            section = chunk.section_title or "Introduction"
            context_parts.append(f"[{idx}] Section: {section}\n{chunk.content}\n")

        return "\n".join(context_parts)

    def _add_citations(self, response: str, chunks: list[DocumentChunk]) -> str:
        """
        Add citation information to the response.

        Args:
            response: Generated response text
            chunks: Retrieved chunks used for context

        Returns:
            Response with citations appended
        """
        # Build citations
        citations = []
        seen_sections = set()

        for chunk in chunks:
            section = chunk.section_title or "Introduction"
            if section not in seen_sections:
                citations.append(f"- {section} ({chunk.source_url})")
                seen_sections.add(section)

        if citations:
            citation_text = "\n\n**Sources:**\n" + "\n".join(citations)
            return response + citation_text

        return response

    def clear_current_page(self) -> None:
        """Clear the currently loaded page."""
        if self.current_collection:
            logger.info(f"Clearing collection: {self.current_collection}")
            self.vector_db.delete_collection(self.current_collection)

        self.current_page_title = None
        self.current_collection = None

    def get_current_page_info(self) -> Optional[dict]:
        """
        Get information about currently loaded page.

        Returns:
            Dictionary with page info or None if no page loaded
        """
        if not self.current_collection:
            return None

        try:
            collection_info = self.vector_db.get_collection_info(self.current_collection)
            return {
                "title": self.current_page_title,
                "collection": self.current_collection,
                "chunk_count": collection_info.get("count", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return None


def get_rag_service() -> RAGService:
    """
    Get a configured RAG service instance.

    Returns:
        Initialized RAGService
    """
    return RAGService()
