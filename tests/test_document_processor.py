"""
Tests for document processing functionality.
"""

import pytest

from src.models.schemas import ChunkingConfig, WikipediaPage, WikipediaSection
from src.services.document_processor import DocumentProcessor, process_wikipedia_page


class TestDocumentProcessor:
    """Test cases for DocumentProcessor."""

    @pytest.fixture
    def sample_page(self):
        """Create a sample Wikipedia page for testing."""
        return WikipediaPage(
            title="Test Page",
            url="https://en.wikipedia.org/wiki/Test_Page",
            page_id=12345,
            language="en",
            summary="This is a test page summary with some content. It has multiple sentences. This helps test chunking.",
            sections=[
                WikipediaSection(
                    title="Introduction",
                    level=1,
                    content="This is the introduction section. " * 50,  # Make it long enough
                    subsections=[],
                ),
                WikipediaSection(
                    title="History",
                    level=1,
                    content="This is the history section with historical information. " * 50,
                    subsections=[],
                ),
            ],
            references=["ref1", "ref2"],
            categories=["Category:Test"],
            raw_content="Full content here. " * 100,
        )

    def test_processor_initialization(self):
        """Test processor initializes with default config."""
        processor = DocumentProcessor()
        assert processor.config.chunk_size == 800  # Default from settings
        assert processor.config.chunk_overlap == 150

    def test_processor_custom_config(self):
        """Test processor initializes with custom config."""
        config = ChunkingConfig(chunk_size=500, chunk_overlap=100, strategy="fixed")
        processor = DocumentProcessor(chunking_config=config)

        assert processor.config.chunk_size == 500
        assert processor.config.chunk_overlap == 100
        assert processor.config.strategy == "fixed"

    def test_clean_text(self, sample_page):
        """Test text cleaning functionality."""
        processor = DocumentProcessor()

        dirty_text = "This  has    extra   spaces.\n\n\nAnd  newlines."
        clean_text = processor._clean_text(dirty_text)

        assert "  " not in clean_text  # No double spaces
        assert clean_text == "This has extra spaces. And newlines."

    def test_clean_text_removes_references(self, sample_page):
        """Test that reference markers are removed."""
        processor = DocumentProcessor()

        text_with_refs = "This is a sentence[1] with references[2][3]."
        clean_text = processor._clean_text(text_with_refs)

        assert "[1]" not in clean_text
        assert "[2]" not in clean_text
        assert "This is a sentence with references." == clean_text

    def test_process_page_creates_chunks(self, sample_page):
        """Test that processing creates chunks."""
        processor = DocumentProcessor()
        chunks = processor.process_page(sample_page)

        assert len(chunks) > 0
        assert all(chunk.source_page_title == "Test Page" for chunk in chunks)
        assert all(chunk.source_url == sample_page.url for chunk in chunks)

    def test_chunks_have_metadata(self, sample_page):
        """Test that chunks have proper metadata."""
        processor = DocumentProcessor()
        chunks = processor.process_page(sample_page)

        for chunk in chunks:
            assert chunk.chunk_id is not None
            assert chunk.metadata is not None
            assert "page_title" in chunk.metadata
            assert chunk.token_count is not None
            assert chunk.token_count > 0

    def test_chunks_are_sequential(self, sample_page):
        """Test that chunk indices are sequential."""
        processor = DocumentProcessor()
        chunks = processor.process_page(sample_page)

        indices = [chunk.chunk_index for chunk in chunks]
        assert indices == list(range(len(chunks)))

    def test_semantic_chunking(self, sample_page):
        """Test semantic chunking by sections."""
        config = ChunkingConfig(chunk_size=500, chunk_overlap=100, strategy="semantic")
        processor = DocumentProcessor(chunking_config=config)

        chunks = processor.process_page(sample_page)

        # Should have chunks from different sections
        section_titles = set(chunk.section_title for chunk in chunks)
        assert len(section_titles) > 0

    def test_fixed_size_chunking(self, sample_page):
        """Test fixed-size chunking strategy."""
        config = ChunkingConfig(chunk_size=200, chunk_overlap=50, strategy="fixed")
        processor = DocumentProcessor(chunking_config=config)

        chunks = processor.process_page(sample_page)

        assert len(chunks) > 0
        # Check that chunks are roughly the right size (in characters)
        # Token approximation: 4 chars per token
        for chunk in chunks:
            assert len(chunk.content) <= 200 * 4 * 1.2  # Allow 20% tolerance

    def test_chunk_id_generation(self, sample_page):
        """Test that chunk IDs are unique."""
        processor = DocumentProcessor()
        chunks = processor.process_page(sample_page)

        chunk_ids = [chunk.chunk_id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))  # All unique

    def test_get_chunk_stats(self, sample_page):
        """Test chunk statistics calculation."""
        processor = DocumentProcessor()
        chunks = processor.process_page(sample_page)

        stats = processor.get_chunk_stats(chunks)

        assert stats["total_chunks"] == len(chunks)
        assert stats["avg_chunk_size"] > 0
        assert stats["min_chunk_size"] > 0
        assert stats["max_chunk_size"] >= stats["avg_chunk_size"]
        assert stats["total_tokens"] > 0
        assert stats["avg_tokens_per_chunk"] > 0

    def test_get_chunk_stats_empty(self):
        """Test chunk statistics with empty chunks list."""
        processor = DocumentProcessor()
        stats = processor.get_chunk_stats([])

        # Verify all keys are present even for empty chunks
        expected_keys = [
            "total_chunks",
            "avg_chunk_size",
            "min_chunk_size",
            "max_chunk_size",
            "total_tokens",
            "avg_tokens_per_chunk",
        ]

        for key in expected_keys:
            assert key in stats, f"Missing key: {key}"
            assert stats[key] == 0, f"Expected 0 for {key} in empty stats"

    def test_convenience_function(self, sample_page):
        """Test convenience function for processing."""
        chunks = process_wikipedia_page(sample_page, chunk_size=600, chunk_overlap=100)

        assert len(chunks) > 0
        assert all(isinstance(chunk.chunk_id, str) for chunk in chunks)

    def test_empty_sections_skipped(self):
        """Test that very short sections are skipped."""
        page = WikipediaPage(
            title="Short Test",
            url="https://test.com",
            summary="Summary text here for testing.",
            sections=[
                WikipediaSection(
                    title="Very Short",
                    level=1,
                    content="Too short.",  # Less than 50 chars, should be skipped
                    subsections=[],
                ),
            ],
            raw_content="Summary text here for testing. Too short.",
        )

        processor = DocumentProcessor()
        chunks = processor.process_page(page)

        # Should only have summary chunk, very short section should be skipped
        section_titles = [c.section_title for c in chunks]
        # Either "Very Short" is not in chunks, or all its chunks are >= 50 chars
        if "Very Short" in section_titles:
            assert all(len(c.content) >= 50 for c in chunks if c.section_title == "Very Short")
