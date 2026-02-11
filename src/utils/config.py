"""
Configuration management for the RAG Wikipedia Chatbot.

Loads and validates configuration from environment variables and .env files.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: str = "lmstudio"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_model: str = "mistral-7b-instruct"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000

    # OpenAI Configuration (Future)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"

    # Azure OpenAI Configuration (Future)
    azure_openai_endpoint: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_deployment: Optional[str] = None

    # Vector Database Configuration
    vector_db: str = "chroma"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_persist_dir: str = "./chroma_data"

    # Weaviate Configuration
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None

    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # RAG Configuration
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k_results: int = 5
    min_similarity_score: float = 0.7

    # Wikipedia Configuration
    wikipedia_language: str = "en"
    user_agent: str = "RAGChatbot/1.0 (Educational Purpose)"

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    @property
    def chroma_client_settings(self) -> dict:
        """Get Chroma client settings."""
        return {
            "host": self.chroma_host,
            "port": self.chroma_port,
        }

    @property
    def is_local_llm(self) -> bool:
        """Check if using local LLM."""
        return self.llm_provider == "lmstudio"

    @property
    def is_cloud_llm(self) -> bool:
        """Check if using cloud LLM."""
        return self.llm_provider in ["openai", "azure"]

    def validate_settings(self) -> None:
        """Validate critical settings."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API key is required when llm_provider=openai")

        if self.llm_provider == "azure" and (
            not self.azure_openai_endpoint or not self.azure_openai_key
        ):
            raise ValueError(
                "Azure OpenAI endpoint and key are required when llm_provider=azure"
            )

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        # Ensure log directory exists
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance with validated configuration
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment (useful for testing).

    Returns:
        Fresh Settings instance
    """
    global _settings
    _settings = Settings()
    _settings.validate_settings()
    return _settings


# Convenience function for getting specific settings
def get_llm_config() -> dict:
    """Get LLM configuration."""
    settings = get_settings()
    return {
        "provider": settings.llm_provider,
        "base_url": settings.lmstudio_base_url,
        "model": settings.lmstudio_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
    }


def get_vector_db_config() -> dict:
    """Get vector database configuration."""
    settings = get_settings()
    if settings.vector_db == "chroma":
        return {
            "type": "chroma",
            "host": settings.chroma_host,
            "port": settings.chroma_port,
            "persist_dir": settings.chroma_persist_dir,
        }
    elif settings.vector_db == "weaviate":
        return {
            "type": "weaviate",
            "url": settings.weaviate_url,
            "api_key": settings.weaviate_api_key,
        }
    else:
        raise ValueError(f"Unsupported vector database: {settings.vector_db}")


def get_embedding_config() -> dict:
    """Get embedding configuration."""
    settings = get_settings()
    return {
        "model_name": settings.embedding_model,
        "device": settings.embedding_device,
    }


def get_chunking_config() -> dict:
    """Get chunking configuration."""
    settings = get_settings()
    return {
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }
