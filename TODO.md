# RAG Wikipedia Chatbot MVP - Development Roadmap

## Project Overview
A RAG-based chatbot that enables users to ask questions about specific Wikipedia pages with documented, source-referenced responses. Built with Python, initially targeting local deployment with LMStudio, designed with adapters for cloud migration.

---

## Technical Stack
- **Language**: Python 3.11+
- **LLM**: LMStudio (local) → Cloud providers via adapters
- **Vector DB**: Chroma/Weaviate (Docker)
- **Orchestration**: Docker Compose
- **RAG Framework**: LangChain or LlamaIndex
- **Web Scraping**: Wikipedia API + BeautifulSoup4/requests

---

## Phase 1: Project Setup & Infrastructure ✅ COMPLETE

### 1.1 Environment Setup ✅
- [x] Initialize Python project with `pyproject.toml` (using uv)
- [x] Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [x] Create `.env.example` for configuration templates
- [x] Set up `pyproject.toml` with core dependencies:
  - `langchain` or `llama-index`
  - `chromadb` or `weaviate-client`
  - `wikipedia-api` or `requests` + `beautifulsoup4`
  - `python-dotenv`
  - `openai` (for LMStudio compatibility)
  - `sentence-transformers`
- [x] Create virtual environment: `uv venv`
- [x] Install dependencies: `uv pip install -e ".[dev]"`
- [x] Create `.gitignore` for Python projects

### 1.2 Docker Compose Setup ✅
- [x] Create `docker-compose.yml` with:
  - Chroma or Weaviate service configuration
  - Volume mounts for persistence
  - Network configuration
  - Environment variables
- [x] Document startup/shutdown procedures (see QUICKSTART.md)
- [x] Test vector DB connectivity (healthchecks configured)

### 1.3 Project Structure ✅
```
rag-example/
├── src/
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── llm_adapter.py          # Abstract LLM interface
│   │   ├── lmstudio_adapter.py     # LMStudio implementation
│   │   ├── openai_adapter.py       # Future: OpenAI/Azure
│   │   └── vectordb_adapter.py     # VectorDB interface
│   ├── services/
│   │   ├── __init__.py
│   │   ├── wikipedia_scraper.py    # Wikipedia data retrieval
│   │   ├── document_processor.py   # Chunking & preprocessing
│   │   ├── embedding_service.py    # Embedding generation
│   │   └── rag_service.py          # Main RAG orchestration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic models
│   └── utils/
│       ├── __init__.py
│       ├── config.py               # Configuration management
│       └── logger.py               # Logging setup
├── tests/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── main.py
```

---

## Phase 2: Wikipedia Data Retrieval & Processing ✅ COMPLETE

### 2.1 Wikipedia Scraper Implementation ✅
- [x] Create `wikipedia_scraper.py`:
  - [x] Method to accept Wikipedia URL or page title
  - [x] Use Wikipedia API for structured data retrieval
  - [x] Fallback to BeautifulSoup for HTML parsing if needed
  - [x] Extract: title, sections, content, references
  - [x] Handle pagination and multi-section articles
  - [x] Error handling for invalid URLs/missing pages

### 2.2 Document Processing Pipeline ✅
- [x] Create `document_processor.py`:
  - [x] Text cleaning (remove HTML artifacts, special characters)
  - [x] Chunking strategy (semantic vs fixed-size):
    - Target: 500-1000 tokens per chunk
    - Overlap: 100-200 tokens
  - [x] Metadata preservation (section titles, references, URLs)
  - [x] Document structure preservation for citations

### 2.3 Testing Data Retrieval ✅
- [x] Test with 3-5 diverse Wikipedia pages:
  - Short article (< 5 sections)
  - Medium article with images/tables
  - Long article (> 20 sections)
- [x] Validate chunk quality and metadata
- [x] Created test suite and demo script

---

## Phase 3: Vector Database Integration

### 3.1 VectorDB Adapter Pattern
- [ ] Create abstract `VectorDBAdapter` interface:
  - `store_documents(documents, embeddings, metadata)`
  - `similarity_search(query_embedding, k=5)`
  - `delete_collection(name)`
  - `get_collection_info()`
  
### 3.2 Chroma Implementation (Primary)
- [ ] Implement `ChromaAdapter`:
  - [ ] Initialize persistent client with Docker connection
  - [ ] Collection creation with metadata
  - [ ] Batch document insertion
  - [ ] Semantic search with filters
- [ ] Configure Chroma in Docker Compose:
  - Persistence volume
  - Port mapping (8000)
  - Environment variables

### 3.3 Weaviate Implementation (Alternative)
- [ ] Implement `WeaviateAdapter`:
  - [ ] Schema definition for Wikipedia documents
  - [ ] Batch import optimization
  - [ ] GraphQL query implementation
- [ ] Configure Weaviate in Docker Compose
- [ ] Document switching between Chroma/Weaviate

---

## Phase 4: Embedding Service

### 4.1 Embedding Generation
- [ ] Create `embedding_service.py`:
  - [ ] Use `sentence-transformers` (e.g., `all-MiniLM-L6-v2` for local)
  - [ ] Batch processing for efficiency
  - [ ] Caching mechanism for repeated embeddings
  - [ ] Support for different embedding models via config

### 4.2 Integration
- [ ] Connect embedding service to document processor
- [ ] Integrate with vector DB adapter
- [ ] Test embedding quality with sample queries

---

## Phase 5: LLM Integration with Adapter Pattern

### 5.1 LLM Adapter Interface
- [ ] Create abstract `LLMAdapter` class:
  - `generate(prompt, context, max_tokens, temperature)`
  - `stream_generate()` for streaming responses
  - `get_model_info()`
  - Error handling and retries

### 5.2 LMStudio Adapter
- [ ] Implement `LMStudioAdapter`:
  - [ ] OpenAI-compatible API client
  - [ ] Default endpoint: `http://localhost:1234/v1`
  - [ ] Model selection configuration
  - [ ] Test with common models (Mistral, Llama 2, etc.)
  
### 5.3 Cloud Adapter Stubs (Future)
- [ ] Create `OpenAIAdapter` stub:
  - [ ] API key management
  - [ ] Model selection (GPT-4, GPT-3.5-turbo)
- [ ] Create `AzureOpenAIAdapter` stub
- [ ] Document migration process from LMStudio → Cloud

### 5.4 Configuration
- [ ] Add to `.env`:
  ```
  LLM_PROVIDER=lmstudio  # lmstudio, openai, azure
  LMSTUDIO_BASE_URL=http://localhost:1234/v1
  LMSTUDIO_MODEL=mistral-7b-instruct
  ```

---

## Phase 6: RAG Service Implementation

### 6.1 Core RAG Logic
- [ ] Create `rag_service.py`:
  - [ ] Query processing:
    - Generate query embedding
    - Retrieve top-k relevant chunks (k=3-5)
  - [ ] Context assembly:
    - Format retrieved chunks with metadata
    - Add source citations
  - [ ] Prompt engineering:
    - System prompt for factual responses
    - Context injection template
    - Citation instructions
  - [ ] Response generation with LLM adapter
  
### 6.2 Citation System
- [ ] Design citation format:
  - Include section names
  - Include Wikipedia URL
  - Chunk reference numbers
- [ ] Post-process responses to add inline citations
- [ ] Validate citations point to correct sources

### 6.3 Conversation History (Optional for MVP)
- [ ] Simple in-memory conversation buffer
- [ ] Context window management
- [ ] Clear history command

---

## Phase 7: CLI Interface (MVP)

### 7.1 Main Application
- [ ] Create `main.py`:
  - [ ] Load Wikipedia page command:
    - `load <url_or_title>` - scrape and index page
  - [ ] Chat interface:
    - `chat` - enter chat mode
    - Display citations with responses
  - [ ] Info commands:
    - `info` - show loaded page info
    - `clear` - clear current index
    - `exit` - quit application

### 7.2 User Flow
```
1. Start application
2. Load Wikipedia page: "Albert Einstein"
3. System processes and indexes content
4. Enter chat mode
5. Ask: "What was Einstein's contribution to quantum theory?"
6. Receive answer with citations
7. Continue conversation or load new page
```

---

## Phase 8: Configuration & Error Handling

### 8.1 Configuration Management
- [ ] Create `config.py`:
  - [ ] Load from `.env` with defaults
  - [ ] Validate required settings
  - [ ] Type-safe configuration class
  
### 8.2 Logging
- [ ] Set up structured logging:
  - [ ] File output for debugging
  - [ ] Console output for user feedback
  - [ ] Different log levels per component

### 8.3 Error Handling
- [ ] Graceful failures for:
  - [ ] Network errors (Wikipedia, LMStudio)
  - [ ] Vector DB connection issues
  - [ ] Invalid Wikipedia pages
  - [ ] LLM generation failures
- [ ] User-friendly error messages

---

## Phase 9: Testing

### 9.1 Unit Tests
- [ ] Test Wikipedia scraper with mock responses
- [ ] Test document chunking logic
- [ ] Test adapter implementations with mocks
- [ ] Test RAG service logic

### 9.2 Integration Tests
- [ ] End-to-end test with real Wikipedia page
- [ ] Test vector DB persistence
- [ ] Test LMStudio integration (if available)

### 9.3 Manual Testing Scenarios
- [ ] Short Wikipedia page (< 1000 words)
- [ ] Long Wikipedia page (> 10,000 words)
- [ ] Page with complex formatting (tables, lists)
- [ ] Test with different LMStudio models
- [ ] Test citation accuracy

---

## Phase 10: Documentation

### 10.1 README.md
- [ ] Project description
- [ ] Prerequisites (Python, Docker, LMStudio)
- [ ] Installation instructions
- [ ] Configuration guide
- [ ] Usage examples
- [ ] Architecture diagram
- [ ] Troubleshooting section

### 10.2 Code Documentation
- [ ] Docstrings for all public methods
- [ ] Type hints throughout
- [ ] Inline comments for complex logic

### 10.3 Migration Guide
- [ ] Document switching between Chroma/Weaviate
- [ ] Document migrating from LMStudio to cloud LLMs
- [ ] Performance tuning tips

---

## Future Enhancements (Post-MVP)

### Browser MCP Integration
- [ ] Research Cursor browser MCP capabilities
- [ ] Implement `browser_mcp_scraper.py`:
  - [ ] Use MCP to navigate to Wikipedia page
  - [ ] Extract content from rendered page
  - [ ] Handle JavaScript-rendered content
  - [ ] Capture dynamic elements not in API
- [ ] Add configuration option: `DATA_SOURCE=api|browser_mcp`
- [ ] Benefits:
  - More accurate rendering
  - Access to interactive elements
  - Better handling of special pages

### Additional Features
- [ ] Web UI (FastAPI + React/Streamlit)
- [ ] Multi-document support (compare multiple Wikipedia pages)
- [ ] Export conversation history
- [ ] Fine-tune embedding model on Wikipedia corpus
- [ ] Implement caching for frequently asked questions
- [ ] Add support for other knowledge sources (docs sites, PDFs)
- [ ] Implement query reformulation for better retrieval
- [ ] Add metadata filtering (date ranges, categories)
- [ ] Response quality evaluation metrics
- [ ] Deployment to cloud (AWS/GCP/Azure)

### Performance Optimizations
- [ ] Async processing for document indexing
- [ ] Connection pooling for vector DB
- [ ] Embedding caching with Redis
- [ ] Query result caching
- [ ] Batch processing for multiple documents

---

## Success Metrics (MVP)

- [ ] Successfully load and index a Wikipedia page in < 30 seconds
- [ ] Answer factual questions with 80%+ relevance
- [ ] Provide accurate citations for all responses
- [ ] Handle at least 3 different Wikipedia pages without restart
- [ ] Gracefully handle network/LLM failures
- [ ] Complete documentation for setup and usage

---

## Development Timeline Estimate

**Phase 1-3**: Infrastructure & Data (Foundation)
**Phase 4-6**: Core RAG Implementation (Core Logic)
**Phase 7-8**: Interface & Reliability (User Experience)
**Phase 9-10**: Testing & Documentation (Polish)

---

## Getting Started (First Steps)

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Create virtual environment: `uv venv`
3. Install dependencies: `uv pip install -e ".[dev]"`
4. Start Docker Compose with Chroma: `docker-compose up -d`
5. Implement Wikipedia scraper
6. Test data retrieval with one page
7. Build incrementally from there

---

## Notes & Decisions

- **Why Chroma as primary?** Simpler setup, Python-native, great for MVP
- **Why adapter pattern?** Future-proof for cloud migration without rewrite
- **Why LMStudio first?** No API costs, full control, privacy
- **Chunking strategy?** Start with fixed-size, optimize based on results
- **Citation format?** [Section Name, Wikipedia URL] inline references
