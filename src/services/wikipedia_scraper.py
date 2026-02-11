"""
Wikipedia scraper for retrieving and parsing Wikipedia pages.

Supports both Wikipedia API and HTML parsing as fallback.
"""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import unquote, urlparse

import requests
import wikipediaapi
from bs4 import BeautifulSoup

from src.models.schemas import WikipediaPage, WikipediaSection
from src.utils.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WikipediaScraperError(Exception):
    """Base exception for Wikipedia scraper errors."""

    pass


class PageNotFoundError(WikipediaScraperError):
    """Raised when a Wikipedia page is not found."""

    pass


class NetworkError(WikipediaScraperError):
    """Raised when network request fails."""

    pass


class WikipediaScraper:
    """
    Scraper for retrieving Wikipedia pages using the Wikipedia API.

    Handles page retrieval, parsing, and error cases gracefully.
    """

    def __init__(self, language: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Initialize the Wikipedia scraper.

        Args:
            language: Wikipedia language code (default: from settings)
            user_agent: Custom user agent (default: from settings)
        """
        settings = get_settings()
        self.language = language or settings.wikipedia_language
        self.user_agent = user_agent or settings.user_agent

        # Initialize Wikipedia API
        self.wiki_api = wikipediaapi.Wikipedia(
            user_agent=self.user_agent,
            language=self.language,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
        )

        logger.info(f"Initialized Wikipedia scraper for language: {self.language}")

    def fetch(self, page_identifier: str) -> WikipediaPage:
        """
        Fetch a Wikipedia page by title or URL.

        Args:
            page_identifier: Wikipedia page title or URL

        Returns:
            WikipediaPage object with parsed content

        Raises:
            PageNotFoundError: If page doesn't exist
            NetworkError: If request fails
        """
        # Extract page title from URL if needed
        page_title = self._extract_title_from_identifier(page_identifier)

        logger.info(f"Fetching Wikipedia page: {page_title}")

        try:
            # Fetch page using Wikipedia API
            page = self.wiki_api.page(page_title)

            if not page.exists():
                logger.error(f"Page not found: {page_title}")
                raise PageNotFoundError(f"Wikipedia page '{page_title}' not found")

            # Parse page content
            wikipedia_page = self._parse_page(page)

            logger.info(
                f"Successfully fetched page: {page_title} "
                f"({wikipedia_page.word_count} words, "
                f"{len(wikipedia_page.sections)} sections)"
            )

            return wikipedia_page

        except PageNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching page {page_title}: {e}", exc_info=True)
            raise NetworkError(f"Failed to fetch Wikipedia page: {e}") from e

    def _extract_title_from_identifier(self, identifier: str) -> str:
        """
        Extract page title from URL or return identifier as-is.

        Args:
            identifier: Wikipedia page title or URL

        Returns:
            Page title
        """
        # If it's a URL, extract the title
        if identifier.startswith("http://") or identifier.startswith("https://"):
            parsed_url = urlparse(identifier)

            # Extract title from URL path
            # Example: https://en.wikipedia.org/wiki/Quantum_mechanics -> Quantum_mechanics
            path_parts = parsed_url.path.split("/")
            if "wiki" in path_parts:
                wiki_index = path_parts.index("wiki")
                if wiki_index + 1 < len(path_parts):
                    title = path_parts[wiki_index + 1]
                    # Decode URL encoding
                    title = unquote(title)
                    # Replace underscores with spaces
                    title = title.replace("_", " ")
                    return title

            raise ValueError(f"Could not extract page title from URL: {identifier}")

        # Otherwise, assume it's already a title
        return identifier

    def _parse_page(self, page: wikipediaapi.WikipediaPage) -> WikipediaPage:
        """
        Parse a Wikipedia API page into our WikipediaPage model.

        Args:
            page: Wikipedia API page object

        Returns:
            WikipediaPage model
        """
        # Extract sections
        sections = self._parse_sections(page.sections)

        # Build full content
        raw_content = self._build_raw_content(page.text, sections)

        # Extract references (basic extraction from text)
        references = self._extract_references(page.text)

        # Extract categories
        categories = list(page.categories.keys()) if hasattr(page, "categories") else []

        return WikipediaPage(
            title=page.title,
            url=page.fullurl,
            page_id=page.pageid if hasattr(page, "pageid") else None,
            language=self.language,
            summary=page.summary,
            sections=sections,
            references=references,
            categories=categories,
            last_modified=None,  # API doesn't provide this easily
            raw_content=raw_content,
        )

    def _parse_sections(
        self, sections: list[wikipediaapi.WikipediaPageSection], level: int = 1
    ) -> list[WikipediaSection]:
        """
        Recursively parse Wikipedia sections.

        Args:
            sections: List of Wikipedia API sections
            level: Current heading level

        Returns:
            List of WikipediaSection models
        """
        parsed_sections = []

        for section in sections:
            # Skip empty sections
            if not section.text or not section.text.strip():
                continue

            # Parse subsections recursively
            subsections = (
                self._parse_sections(section.sections, level + 1) if section.sections else []
            )

            parsed_section = WikipediaSection(
                title=section.title,
                level=level,
                content=section.text.strip(),
                subsections=subsections,
            )

            parsed_sections.append(parsed_section)

        return parsed_sections

    def _build_raw_content(self, main_text: str, sections: list[WikipediaSection]) -> str:
        """
        Build complete raw content from page text and sections.

        Args:
            main_text: Main page text from API
            sections: Parsed sections

        Returns:
            Complete page content as string
        """
        content_parts = [main_text]

        def add_section_content(section: WikipediaSection):
            content_parts.append(f"\n\n{'#' * section.level} {section.title}\n\n{section.content}")
            for subsection in section.subsections:
                add_section_content(subsection)

        for section in sections:
            add_section_content(section)

        return "\n".join(content_parts)

    def _extract_references(self, text: str) -> list[str]:
        """
        Extract references from text (basic implementation).

        Args:
            text: Page text

        Returns:
            List of reference strings
        """
        # This is a simplified approach
        # In a full implementation, you'd parse the actual references section
        references = []

        # Look for common reference patterns
        ref_patterns = [
            r"\[(\d+)\]",  # [1], [2], etc.
            r"(https?://[^\s]+)",  # URLs
        ]

        for pattern in ref_patterns:
            matches = re.findall(pattern, text)
            references.extend(matches)

        # Remove duplicates and limit
        return list(set(references))[:50]

    def search_pages(self, query: str, limit: int = 10) -> list[str]:
        """
        Search for Wikipedia pages matching a query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of page titles
        """
        logger.info(f"Searching Wikipedia for: {query}")

        try:
            # Use Wikipedia API search
            url = f"https://{self.language}.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": query,
                "limit": limit,
                "format": "json",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            # OpenSearch returns [query, [titles], [descriptions], [urls]]
            titles = data[1] if len(data) > 1 else []

            logger.info(f"Found {len(titles)} results for query: {query}")
            return titles

        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}", exc_info=True)
            return []

    def get_page_info(self, page_title: str) -> Optional[dict]:
        """
        Get basic information about a page without fetching full content.

        Args:
            page_title: Wikipedia page title

        Returns:
            Dictionary with page info or None if not found
        """
        try:
            page = self.wiki_api.page(page_title)

            if not page.exists():
                return None

            return {
                "title": page.title,
                "url": page.fullurl,
                "summary": page.summary[:200] + "..." if len(page.summary) > 200 else page.summary,
                "exists": True,
            }

        except Exception as e:
            logger.error(f"Error getting page info: {e}", exc_info=True)
            return None


# Convenience function
def fetch_wikipedia_page(page_identifier: str, language: str = "en") -> WikipediaPage:
    """
    Convenience function to fetch a Wikipedia page.

    Args:
        page_identifier: Wikipedia page title or URL
        language: Wikipedia language code

    Returns:
        WikipediaPage object

    Raises:
        PageNotFoundError: If page doesn't exist
        NetworkError: If request fails
    """
    scraper = WikipediaScraper(language=language)
    return scraper.fetch(page_identifier)
