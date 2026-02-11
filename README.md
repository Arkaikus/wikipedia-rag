# RAG Wikipedia Chatbot MVP

A RAG (Retrieval-Augmented Generation) chatbot that enables intelligent Q&A on any Wikipedia page with source-cited responses.

## Overview

This MVP allows you to:
- Load any Wikipedia page by URL or title
- Ask questions about the content
- Receive AI-generated answers with accurate citations
- Run completely locally with LMStudio
- Migrate to cloud LLMs when needed (adapter pattern)

## Architecture

```
User Query → Embedding → Vector Search → Context Retrieval → LLM → Cited Response
                ↓                              ↑
            Chroma/Weaviate              Wikipedia Content
```

**Key Design Decisions:**
- **Adapter Pattern**: Easy migration from LMStudio to cloud providers
- **Docker Compose**: Self-hosted vector DB for data control
- **Modular Services**: Clear separation of concerns for maintainability

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (fast Python package installer)
- Docker & Docker Compose
- [LMStudio](https://lmstudio.ai/) (running locally with server enabled)
- 8GB+ RAM recommended

## Quick Start

### 1. Setup Environment

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or with pip: pip install uv

# Clone/navigate to project
cd rag-example

# Create virtual environment and install dependencies (uv handles both!)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project with dependencies
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Start Vector Database

```bash
# Start Chroma in Docker
docker-compose up -d

# Verify it's running
docker-compose ps
```

### 3. Start LMStudio

1. Open LMStudio
2. Load a model (recommended: Mistral 7B Instruct or Llama 2 7B Chat)
3. Start the local server (default port: 1234)
4. Verify at http://localhost:1234/v1/models

### 4. Run the Chatbot

```bash
python main.py
```

## Usage Example

```
> load "Quantum Mechanics"
Loading Wikipedia page...
Processing 127 chunks...
Indexing complete!

> chat
You: What is the uncertainty principle?
Assistant: The uncertainty principle, formulated by Werner Heisenberg, 
states that... [Quantum Mechanics - Uncertainty Principle, https://...]
```

## Documentation

- **[TODO.md](TODO.md)** - Complete development roadmap (10 phases)
- **[QUICKSTART.md](QUICKSTART.md)** - Get running in under 10 minutes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and patterns
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow and best practices
- **[MIGRATION.md](MIGRATION.md)** - Guide for migrating to cloud services
- **[UV_GUIDE.md](UV_GUIDE.md)** - Quick reference for uv package manager

## Technology Stack

- **Package Manager**: uv (10-100x faster than pip!)
- **Language**: Python 3.11+
- **RAG Framework**: LangChain
- **Vector DB**: ChromaDB (Docker) / Weaviate (alternative)
- **LLM**: LMStudio (local) → OpenAI/Azure (cloud adapters)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Web Scraping**: Wikipedia API + BeautifulSoup4

## Project Status

🚧 **MVP Development Phase** - Following TODO.md roadmap

Current: Project structure and documentation complete
Next: Implement Wikipedia scraper (Phase 2)

## Contributing

This is an MVP project. Development follows the roadmap in TODO.md.

## License

MIT License - Feel free to use and modify for your projects!