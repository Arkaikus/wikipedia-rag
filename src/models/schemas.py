"""
Data models and schemas for the RAG Wikipedia Chatbot.

These Pydantic models ensure type safety and validation throughout the application.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class WikipediaSection(BaseModel):
    """Represents a section within a Wikipedia page."""

    title: str = Field(..., description="Section title")
    level: int = Field(..., ge=1, le=6, description="Heading level (1-6)")
    content: str = Field(..., description="Section content")
    subsections: list["WikipediaSection"] = Field(
        default_factory=list, description="Nested subsections"
    )

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v or not v.strip():
            raise ValueError("Section content cannot be empty")
        return v.strip()


class WikipediaPage(BaseModel):
    """Represents a complete Wikipedia page."""

    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Wikipedia page URL")
    page_id: Optional[int] = Field(None, description="Wikipedia page ID")
    language: str = Field(default="en", description="Language code")
    summary: str = Field(..., description="Page summary/introduction")
    sections: list[WikipediaSection] = Field(
        default_factory=list, description="Page sections"
    )
    references: list[str] = Field(default_factory=list, description="References/citations")
    categories: list[str] = Field(default_factory=list, description="Page categories")
    last_modified: Optional[datetime] = Field(None, description="Last modification date")
    raw_content: str = Field(..., description="Full page content as text")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is valid."""
        if not v.startswith("http"):
            raise ValueError("URL must start with http or https")
        return v

    @property
    def full_text(self) -> str:
        """Get all text content including title and sections."""
        return f"{self.title}\n\n{self.summary}\n\n{self.raw_content}"

    @property
    def word_count(self) -> int:
        """Count total words in the page."""
        return len(self.full_text.split())


class DocumentChunk(BaseModel):
    """Represents a chunk of text from a document."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="Chunk text content")
    metadata: dict[str, str] = Field(default_factory=dict, description="Chunk metadata")
    source_page_title: str = Field(..., description="Source Wikipedia page title")
    source_url: str = Field(..., description="Source Wikipedia page URL")
    section_title: Optional[str] = Field(None, description="Section this chunk belongs to")
    chunk_index: int = Field(..., ge=0, description="Position in document (0-indexed)")
    token_count: Optional[int] = Field(None, description="Approximate token count")

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v or not v.strip():
            raise ValueError("Chunk content cannot be empty")
        return v

    def to_langchain_document(self) -> dict:
        """Convert to LangChain Document format."""
        return {
            "page_content": self.content,
            "metadata": {
                **self.metadata,
                "source": self.source_url,
                "title": self.source_page_title,
                "section": self.section_title or "Main",
                "chunk_id": self.chunk_id,
                "chunk_index": self.chunk_index,
            },
        }


class QueryResult(BaseModel):
    """Represents a query result with retrieved context."""

    query: str = Field(..., description="Original query text")
    retrieved_chunks: list[DocumentChunk] = Field(
        default_factory=list, description="Retrieved document chunks"
    )
    similarity_scores: list[float] = Field(
        default_factory=list, description="Similarity scores for each chunk"
    )
    context: str = Field(..., description="Assembled context from chunks")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @property
    def num_chunks(self) -> int:
        """Number of retrieved chunks."""
        return len(self.retrieved_chunks)

    @property
    def sources(self) -> list[str]:
        """Unique source URLs from retrieved chunks."""
        return list(set(chunk.source_url for chunk in self.retrieved_chunks))


class ChatMessage(BaseModel):
    """Represents a chat message."""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    citations: list[str] = Field(default_factory=list, description="Source citations")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Ensure role is valid."""
        if v not in ["user", "assistant", "system"]:
            raise ValueError("Role must be one of: user, assistant, system")
        return v


class ChatSession(BaseModel):
    """Represents a chat session with conversation history."""

    session_id: str = Field(..., description="Unique session identifier")
    page_title: Optional[str] = Field(None, description="Currently loaded Wikipedia page")
    page_url: Optional[str] = Field(None, description="Currently loaded page URL")
    messages: list[ChatMessage] = Field(default_factory=list, description="Conversation history")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    last_activity: datetime = Field(
        default_factory=datetime.now, description="Last activity timestamp"
    )

    def add_message(self, role: str, content: str, citations: Optional[list[str]] = None) -> None:
        """Add a message to the conversation history."""
        message = ChatMessage(role=role, content=content, citations=citations or [])
        self.messages.append(message)
        self.last_activity = datetime.now()

    @property
    def message_count(self) -> int:
        """Total number of messages in session."""
        return len(self.messages)

    def get_recent_messages(self, limit: int = 10) -> list[ChatMessage]:
        """Get the most recent N messages."""
        return self.messages[-limit:]


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""

    model_name: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")
    device: str = Field(default="cpu", description="Device: cpu or cuda")
    batch_size: int = Field(default=32, ge=1, description="Batch size for embedding generation")
    normalize_embeddings: bool = Field(
        default=True, description="Whether to normalize embeddings"
    )


class ChunkingConfig(BaseModel):
    """Configuration for document chunking."""

    chunk_size: int = Field(default=800, ge=100, le=2000, description="Target chunk size in tokens")
    chunk_overlap: int = Field(
        default=150, ge=0, le=500, description="Overlap between chunks in tokens"
    )
    strategy: str = Field(
        default="semantic", description="Chunking strategy: semantic or fixed"
    )

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Ensure strategy is valid."""
        if v not in ["semantic", "fixed", "hybrid"]:
            raise ValueError("Strategy must be one of: semantic, fixed, hybrid")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 800)
        if v >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        return v


class RAGConfig(BaseModel):
    """Configuration for RAG pipeline."""

    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    min_similarity_score: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score threshold"
    )
    llm_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="LLM temperature parameter"
    )
    llm_max_tokens: int = Field(
        default=1000, ge=50, le=4000, description="Maximum tokens in LLM response"
    )
    include_citations: bool = Field(default=True, description="Include citations in responses")
