# Architecture Documentation

## System Overview

The RAG Wikipedia Chatbot follows a modular, adapter-based architecture designed for local deployment with cloud migration capabilities.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                        (CLI / Future Web)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RAG Service (Core)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Query        │  │ Context      │  │ Response            │  │
│  │ Processing   │─▶│ Assembly     │─▶│ Generation          │  │
│  └──────────────┘  └──────────────┘  └─────────────────────┘  │
└───────┬─────────────────────┬─────────────────────┬────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Embedding   │   │   Vector DB     │   │   LLM Adapter   │
│  Service     │   │   Adapter       │   │                 │
└──────────────┘   └─────────────────┘   └─────────────────┘
        │                     │                     │
        │                     ▼                     ▼
        │          ┌─────────────────┐   ┌─────────────────┐
        │          │  Chroma/        │   │  LMStudio/      │
        │          │  Weaviate       │   │  OpenAI/Azure   │
        │          │  (Docker)       │   │                 │
        │          └─────────────────┘   └─────────────────┘
        │                     ▲
        │                     │
        ▼                     │
┌──────────────────────────────────────┐
│      Document Processing Pipeline     │
│  ┌────────────┐  ┌─────────────────┐ │
│  │ Wikipedia  │─▶│ Text Chunking & │ │
│  │ Scraper    │  │ Embedding       │─┘
│  └────────────┘  └─────────────────┘  │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────┐
│  Wikipedia API / │
│  HTML Parser     │
└──────────────────┘
```

## Component Details

### 1. RAG Service (Core Orchestrator)
**Responsibility**: Coordinate the RAG pipeline from query to response

**Key Functions**:
- Accept user queries
- Generate query embeddings
- Retrieve relevant context from vector DB
- Format prompts with context and citations
- Generate responses via LLM adapter
- Post-process responses with source citations

**Dependencies**: Embedding Service, VectorDB Adapter, LLM Adapter

---

### 2. LLM Adapter (Interface Pattern)
**Responsibility**: Abstract LLM provider implementation

**Interface**:
```python
class LLMAdapter(ABC):
    @abstractmethod
    def generate(prompt: str, context: str, **kwargs) -> str
    
    @abstractmethod
    def get_model_info() -> dict
```

**Implementations**:
- `LMStudioAdapter`: OpenAI-compatible API to local LMStudio
- `OpenAIAdapter`: Direct OpenAI API integration (future)
- `AzureOpenAIAdapter`: Azure OpenAI Service (future)

**Benefits**:
- Zero code changes to switch LLM providers
- Easy A/B testing between models
- Cost optimization by mixing local/cloud

---

### 3. Vector DB Adapter (Interface Pattern)
**Responsibility**: Abstract vector database operations

**Interface**:
```python
class VectorDBAdapter(ABC):
    @abstractmethod
    def store_documents(docs, embeddings, metadata)
    
    @abstractmethod
    def similarity_search(query_embedding, k=5) -> List[Document]
    
    @abstractmethod
    def delete_collection(name)
```

**Implementations**:
- `ChromaAdapter`: ChromaDB integration (primary)
- `WeaviateAdapter`: Weaviate integration (alternative)

**Benefits**:
- Easy migration between vector DBs
- Performance testing different solutions
- Future support for cloud vector DBs (Pinecone, Qdrant, etc.)

---

### 4. Wikipedia Scraper
**Responsibility**: Retrieve and parse Wikipedia content

**Data Flow**:
1. Accept Wikipedia URL or page title
2. Fetch via Wikipedia API (preferred) or HTML scraping
3. Extract: title, sections, content, references, metadata
4. Return structured document

**Error Handling**:
- Invalid URLs → user-friendly error
- Missing pages → suggest alternatives
- Network errors → retry with backoff

---

### 5. Document Processing Pipeline
**Responsibility**: Transform raw Wikipedia content into vector DB entries

**Steps**:
1. **Text Cleaning**: Remove HTML, special characters, formatting artifacts
2. **Chunking**: 
   - Strategy: Semantic (section-based) + fixed-size fallback
   - Size: 800 tokens per chunk
   - Overlap: 150 tokens
3. **Metadata Attachment**: Section title, URL, references
4. **Embedding Generation**: Convert chunks to vectors
5. **Storage**: Insert into vector DB with metadata

---

### 6. Embedding Service
**Responsibility**: Generate vector embeddings for text

**Model**: `sentence-transformers/all-MiniLM-L6-v2` (default)
- Dimensions: 384
- Fast inference on CPU
- Good general-purpose performance

**Features**:
- Batch processing for efficiency
- Caching for repeated text
- Model configurable via environment

**Future**: Support for OpenAI embeddings, custom fine-tuned models

---

## Data Flow: Indexing a Wikipedia Page

```
1. User: "load Quantum Mechanics"
          ↓
2. Wikipedia Scraper fetches page
          ↓
3. Document Processor:
   - Cleans text
   - Splits into 127 chunks
   - Preserves metadata (sections, refs)
          ↓
4. Embedding Service:
   - Generates 127 embeddings
   - Batch processes for speed
          ↓
5. Vector DB Adapter:
   - Stores chunks + embeddings + metadata
   - Creates searchable index
          ↓
6. User: "Indexing complete! Ready to chat."
```

---

## Data Flow: Answering a Question

```
1. User: "What is the uncertainty principle?"
          ↓
2. RAG Service:
   - Generate query embedding
          ↓
3. Vector DB Adapter:
   - Similarity search (top 5 chunks)
   - Returns: chunks + metadata + scores
          ↓
4. RAG Service:
   - Assemble context from chunks
   - Format prompt:
     System: "You are a helpful assistant..."
     Context: [Chunk 1] [Chunk 2] [Chunk 3]...
     Query: "What is the uncertainty principle?"
     Instructions: "Cite sources using [Section, URL]"
          ↓
5. LLM Adapter:
   - Send to LMStudio/OpenAI
   - Generate response
          ↓
6. RAG Service:
   - Post-process citations
   - Format for display
          ↓
7. User: Receives answer with inline citations
```

---

## Key Design Patterns

### 1. Adapter Pattern
**Used For**: LLM, Vector DB
**Benefit**: Swap implementations without changing business logic

### 2. Dependency Injection
**Used For**: Services receive adapters via constructor
**Benefit**: Testability, loose coupling

### 3. Pipeline Pattern
**Used For**: Document processing
**Benefit**: Clear stages, easy to extend

### 4. Strategy Pattern
**Used For**: Chunking strategies, embedding models
**Benefit**: Runtime configuration

---

## Configuration Management

All components configured via `.env`:

```
# LLM Provider Selection
LLM_PROVIDER=lmstudio  → loads LMStudioAdapter

# Vector DB Selection
VECTOR_DB=chroma  → loads ChromaAdapter

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2 → loads from sentence-transformers
```

Factory pattern used to instantiate correct adapter based on config.

---

## Scaling Considerations

### Current (MVP):
- Single Wikipedia page at a time
- Synchronous processing
- In-memory conversation history
- Local LLM

### Future Optimizations:
- **Multi-document support**: Index multiple pages, search across all
- **Async processing**: Non-blocking document indexing
- **Caching**: Query result caching with Redis
- **Streaming**: Stream LLM responses token-by-token
- **Cloud deployment**: Containerize entire stack
- **API layer**: FastAPI for programmatic access

---

## Technology Choices Rationale

### Why Chroma (Primary)?
- ✅ Python-native, simple setup
- ✅ No external dependencies beyond Docker
- ✅ Good for MVP, scales to production
- ✅ Active community, good docs

### Why LMStudio First?
- ✅ No API costs during development
- ✅ Full privacy, local data
- ✅ Test with multiple models easily
- ✅ OpenAI-compatible API (easy migration)

### Why LangChain/LlamaIndex?
- ✅ Batteries-included RAG toolkit
- ✅ Handles prompt templates, chains, memory
- ✅ Integrations with all major LLMs/VectorDBs
- ✅ Active development, large community

### Why Adapter Pattern?
- ✅ Future-proof: Add providers without refactoring
- ✅ Testing: Mock adapters for unit tests
- ✅ Cost optimization: Mix local/cloud based on load

---

## Security Considerations

### Current:
- ✅ Environment variables for sensitive config
- ✅ `.env` in `.gitignore`
- ✅ No API keys in code

### Future (Production):
- [ ] Use secrets management (AWS Secrets Manager, Vault)
- [ ] API rate limiting
- [ ] Input sanitization for Wikipedia URLs
- [ ] Authentication for web interface
- [ ] Audit logging

---

## Future: Browser MCP Integration

**Planned Enhancement**:

```
Current: Wikipedia API → Document Processor
Future:  Browser MCP → Wikipedia Page → Document Processor
```

**Benefits**:
- Access JavaScript-rendered content
- Capture dynamic elements
- Better handling of complex pages
- Visual verification during scraping

**Implementation**:
- Add `browser_mcp_scraper.py`
- Config: `DATA_SOURCE=api|browser_mcp`
- Fallback to API if MCP fails

---

## Monitoring & Observability (Future)

- **Metrics**: Query latency, embedding time, LLM tokens used
- **Logging**: Structured logs (JSON) for all components
- **Tracing**: OpenTelemetry for request tracing
- **Alerting**: Failed queries, DB connection issues

---

## Testing Strategy

### Unit Tests:
- Mock adapters
- Test business logic in isolation
- Test chunking algorithms

### Integration Tests:
- Real Wikipedia page end-to-end
- Docker Compose with test containers
- Verify vector DB persistence

### Manual Testing:
- Diverse Wikipedia pages (short, long, complex)
- Different LLM models
- Citation accuracy validation
