"""
Tests for Wikipedia scraper functionality.
"""

import pytest

from src.services.wikipedia_scraper import (
    PageNotFoundError,
    WikipediaScraper,
    fetch_wikipedia_page,
)


class TestWikipediaScraper:
    """Test cases for WikipediaScraper."""

    def test_scraper_initialization(self):
        """Test scraper initializes correctly."""
        scraper = WikipediaScraper(language="en")
        assert scraper.language == "en"
        assert scraper.user_agent is not None

    def test_extract_title_from_url(self):
        """Test extracting title from Wikipedia URL."""
        scraper = WikipediaScraper()

        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        title = scraper._extract_title_from_identifier(url)
        assert title == "Python (programming language)"

    def test_extract_title_from_plain_text(self):
        """Test that plain text title is returned as-is."""
        scraper = WikipediaScraper()

        title = scraper._extract_title_from_identifier("Albert Einstein")
        assert title == "Albert Einstein"

    def test_fetch_existing_page(self):
        """Test fetching a real Wikipedia page."""
        scraper = WikipediaScraper()

        page = scraper.fetch("Python (programming language)")

        assert page.title is not None
        assert "Python" in page.title
        assert page.url is not None
        assert len(page.summary) > 0
        assert len(page.raw_content) > 0
        assert page.word_count > 100

    def test_fetch_page_by_url(self):
        """Test fetching a page by URL."""
        scraper = WikipediaScraper()

        page = scraper.fetch("https://en.wikipedia.org/wiki/Artificial_intelligence")

        assert "Artificial intelligence" in page.title
        assert len(page.sections) > 0

    def test_fetch_nonexistent_page(self):
        """Test that fetching non-existent page raises error."""
        scraper = WikipediaScraper()

        with pytest.raises(PageNotFoundError):
            scraper.fetch("ThisPageDefinitelyDoesNotExist12345")

    @pytest.mark.skip(reason="high chances of 403 Forbidden")
    def test_search_pages(self):
        """Test searching for Wikipedia pages."""
        scraper = WikipediaScraper()

        results = scraper.search_pages("quantum mechanics", limit=5)

        assert len(results) > 0
        assert any("quantum" in r.lower() for r in results)

    def test_get_page_info(self):
        """Test getting page info without full content."""
        scraper = WikipediaScraper()

        info = scraper.get_page_info("Python (programming language)")

        assert info is not None
        assert info["exists"] is True
        assert "Python" in info["title"]
        assert info["url"] is not None

    def test_convenience_function(self):
        """Test convenience function for fetching pages."""
        page = fetch_wikipedia_page("Machine learning")

        assert page.title is not None
        assert "learning" in page.title.lower()
        assert len(page.sections) > 0
