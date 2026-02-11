"""
Document processing pipeline for chunking and preprocessing Wikipedia content.

Handles text cleaning, chunking strategies, and metadata preservation.
"""

import hashlib
import re
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.models.schemas import ChunkingConfig, DocumentChunk, WikipediaPage, WikipediaSection
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """
    Processes Wikipedia pages into chunks suitable for vector storage.

    Handles text cleaning, chunking, and metadata preservation.
    """

    def __init__(self, chunking_config: Optional[ChunkingConfig] = None):
        """
        Initialize the document processor.

        Args:
            chunking_config: Configuration for chunking strategy
        """
        if chunking_config is None:
            settings = get_settings()
            chunking_config = ChunkingConfig(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                strategy="semantic",
            )

        self.config = chunking_config

        # Initialize text splitter
        # Using character-based splitting with token approximation
        # Rule of thumb: ~4 characters per token
        char_chunk_size = self.config.chunk_size * 4
        char_overlap = self.config.chunk_overlap * 4

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=char_chunk_size,
            chunk_overlap=char_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            is_separator_regex=False,
        )

        logger.info(
            f"Initialized document processor with chunk_size={self.config.chunk_size}, "
            f"overlap={self.config.chunk_overlap}, strategy={self.config.strategy}"
        )

    def process_page(self, page: WikipediaPage) -> list[DocumentChunk]:
        """
        Process a Wikipedia page into document chunks.

        Args:
            page: WikipediaPage to process

        Returns:
            List of DocumentChunk objects
        """
        logger.info(f"Processing page: {page.title}")

        # Clean the content
        cleaned_content = self._clean_text(page.raw_content)

        # Choose chunking strategy
        if self.config.strategy == "semantic":
            chunks = self._chunk_by_sections(page, cleaned_content)
        elif self.config.strategy == "fixed":
            chunks = self._chunk_fixed_size(page, cleaned_content)
        else:  # hybrid
            chunks = self._chunk_hybrid(page, cleaned_content)

        logger.info(
            f"Processed page '{page.title}' into {len(chunks)} chunks "
            f"(avg {sum(len(c.content) for c in chunks) // len(chunks) if chunks else 0} chars)"
        )

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing unwanted characters and formatting.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special Wikipedia markup that might have leaked through
        text = re.sub(r"\{\{[^}]+\}\}", "", text)  # Remove {{templates}}
        text = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", text)  # Simplify [[links]]

        # Remove reference markers like [1], [2], etc.
        text = re.sub(r"\[\d+\]", "", text)

        # Remove excessive punctuation
        text = re.sub(r"\.{3,}", "...", text)

        # Clean up extra spaces
        text = " ".join(text.split())

        return text.strip()

    def _chunk_fixed_size(self, page: WikipediaPage, content: str) -> list[DocumentChunk]:
        """
        Chunk content using fixed-size strategy.

        Args:
            page: Wikipedia page
            content: Cleaned content

        Returns:
            List of chunks
        """
        # Split text using LangChain's text splitter
        text_chunks = self.text_splitter.split_text(content)

        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunk = self._create_chunk(
                content=chunk_text,
                page=page,
                section_title=None,
                chunk_index=idx,
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_sections(self, page: WikipediaPage, content: str) -> list[DocumentChunk]:
        """
        Chunk content by semantic sections from Wikipedia structure.

        Args:
            page: Wikipedia page with sections
            content: Cleaned content

        Returns:
            List of chunks
        """
        chunks = []
        chunk_index = 0

        # Process introduction/summary separately
        if page.summary:
            summary_chunks = self.text_splitter.split_text(self._clean_text(page.summary))
            for summary_chunk in summary_chunks:
                chunk = self._create_chunk(
                    content=summary_chunk,
                    page=page,
                    section_title="Introduction",
                    chunk_index=chunk_index,
                )
                chunks.append(chunk)
                chunk_index += 1

        # Process each section
        for section in page.sections:
            section_chunks = self._process_section(page, section, chunk_index)
            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)

        return chunks

    def _process_section(
        self, page: WikipediaPage, section: WikipediaSection, start_index: int
    ) -> list[DocumentChunk]:
        """
        Process a single section and its subsections.

        Args:
            page: Wikipedia page
            section: Section to process
            start_index: Starting chunk index

        Returns:
            List of chunks from this section
        """
        chunks = []
        chunk_index = start_index

        # Clean and split section content
        cleaned_content = self._clean_text(section.content)

        if cleaned_content:
            section_chunks = self.text_splitter.split_text(cleaned_content)

            for chunk_text in section_chunks:
                # Skip very short chunks (less than 50 characters)
                if len(chunk_text.strip()) < 50:
                    continue

                chunk = self._create_chunk(
                    content=chunk_text,
                    page=page,
                    section_title=section.title,
                    chunk_index=chunk_index,
                )
                chunks.append(chunk)
                chunk_index += 1

        # Process subsections recursively
        for subsection in section.subsections:
            subsection_chunks = self._process_section(page, subsection, chunk_index)
            chunks.extend(subsection_chunks)
            chunk_index += len(subsection_chunks)

        return chunks

    def _chunk_hybrid(self, page: WikipediaPage, content: str) -> list[DocumentChunk]:
        """
        Hybrid chunking: try semantic first, fall back to fixed-size for large sections.

        Args:
            page: Wikipedia page
            content: Cleaned content

        Returns:
            List of chunks
        """
        # For MVP, use semantic chunking (same as section-based)
        # In future, could implement more sophisticated hybrid logic
        return self._chunk_by_sections(page, content)

    def _create_chunk(
        self,
        content: str,
        page: WikipediaPage,
        section_title: Optional[str],
        chunk_index: int,
    ) -> DocumentChunk:
        """
        Create a DocumentChunk with proper metadata.

        Args:
            content: Chunk content
            page: Source Wikipedia page
            section_title: Section this chunk belongs to
            chunk_index: Index of this chunk in the document

        Returns:
            DocumentChunk object
        """
        # Generate unique chunk ID
        chunk_id = self._generate_chunk_id(page.title, chunk_index)

        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        token_count = len(content) // 4

        # Build metadata
        metadata = {
            "page_title": page.title,
            "page_url": page.url,
            "section": section_title or "Introduction",
            "language": page.language,
            "chunk_index": str(chunk_index),
        }

        return DocumentChunk(
            chunk_id=chunk_id,
            content=content,
            metadata=metadata,
            source_page_title=page.title,
            source_url=page.url,
            section_title=section_title,
            chunk_index=chunk_index,
            token_count=token_count,
        )

    def _generate_chunk_id(self, page_title: str, chunk_index: int) -> str:
        """
        Generate a unique chunk ID.

        Args:
            page_title: Wikipedia page title
            chunk_index: Chunk index

        Returns:
            Unique chunk ID
        """
        # Create a hash from page title for uniqueness
        title_hash = hashlib.md5(page_title.encode()).hexdigest()[:8]
        return f"{title_hash}_{chunk_index:04d}"

    def get_chunk_stats(self, chunks: list[DocumentChunk]) -> dict:
        """
        Calculate statistics about chunks.

        Args:
            chunks: List of document chunks

        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "total_tokens": 0,
                "avg_tokens_per_chunk": 0,
            }

        chunk_sizes = [len(chunk.content) for chunk in chunks]
        token_counts = [chunk.token_count or 0 for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) // len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_chunk": sum(token_counts) // len(token_counts),
        }


# Convenience function
def process_wikipedia_page(
    page: WikipediaPage, chunk_size: int = 800, chunk_overlap: int = 150
) -> list[DocumentChunk]:
    """
    Convenience function to process a Wikipedia page into chunks.

    Args:
        page: WikipediaPage to process
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens

    Returns:
        List of DocumentChunk objects
    """
    config = ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy="semantic",
    )
    processor = DocumentProcessor(chunking_config=config)
    return processor.process_page(page)
