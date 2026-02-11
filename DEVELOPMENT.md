# Development Guide

## Development Workflow

### Using Make (Recommended)

We provide a Makefile for common tasks:

```bash
make help           # Show all available commands
make setup          # Complete initial setup
make dev            # Quick dev setup (install + docker)
make test           # Run tests
make quality        # Run all quality checks
make run            # Run the application
```

### Daily Development Cycle

1. **Start infrastructure**
   ```bash
   make docker-up    # Or: docker-compose up -d
   # Start LMStudio manually
   ```

2. **Activate environment**
   ```bash
   source .venv/bin/activate
   ```

3. **Run tests**
   ```bash
   make test         # Or: pytest tests/ -v
   ```

4. **Develop & iterate**
   ```bash
   make run          # Or: python main.py
   ```

5. **Code quality checks**
   ```bash
   make quality      # Runs format, lint, type-check, test
   # Or individually:
   make format       # black + ruff --fix
   make lint         # ruff check
   make type-check   # mypy
   ```

6. **Stop infrastructure** (when done)
   ```bash
   make docker-down  # Or: docker-compose down
   ```

---

## Recommended Development Order

Follow this sequence for optimal learning curve:

### Phase 1: Data Foundation (Days 1-2)
1. **Wikipedia Scraper** (`src/services/wikipedia_scraper.py`)
   - Start here - most independent component
   - Test with: `pytest tests/test_wikipedia_scraper.py`
   - Validate output manually

2. **Document Processor** (`src/services/document_processor.py`)
   - Depends on: Wikipedia Scraper
   - Test chunking with different sizes
   - Verify metadata preservation

### Phase 2: Storage Layer (Days 3-4)
3. **Vector DB Adapter Interface** (`src/adapters/vectordb_adapter.py`)
   - Define abstract base class
   - Document interface contract

4. **Chroma Adapter** (`src/adapters/chroma_adapter.py`)
   - Implement concrete adapter
   - Test with Docker Compose
   - Verify persistence

5. **Embedding Service** (`src/services/embedding_service.py`)
   - Load sentence-transformers model
   - Test batch processing
   - Measure performance

### Phase 3: LLM Integration (Days 5-6)
6. **LLM Adapter Interface** (`src/adapters/llm_adapter.py`)
   - Define abstract base class
   - Plan for multiple providers

7. **LMStudio Adapter** (`src/adapters/lmstudio_adapter.py`)
   - OpenAI-compatible client
   - Test with running LMStudio
   - Handle errors gracefully

### Phase 4: RAG Core (Days 7-8)
8. **RAG Service** (`src/services/rag_service.py`)
   - Orchestrate all components
   - Implement query → response pipeline
   - Add citation logic

### Phase 5: Interface (Days 9-10)
9. **CLI Implementation** (`main.py`)
   - Command parsing
   - User interaction loop
   - Pretty output with Rich

10. **Documentation & Polish**
    - README updates
    - Usage examples
    - Troubleshooting guide

---

## Testing Strategy

### Unit Tests
```python
# tests/test_wikipedia_scraper.py
def test_scraper_extracts_title():
    scraper = WikipediaScraper()
    result = scraper.fetch("Python (programming language)")
    assert result.title == "Python (programming language)"
```

### Integration Tests
```python
# tests/test_integration.py
def test_end_to_end_flow():
    # Load page → Process → Index → Query → Response
    pass
```

### Manual Testing Checklist
- [ ] Load short Wikipedia page (< 1000 words)
- [ ] Load long Wikipedia page (> 10,000 words)
- [ ] Ask factual question with known answer
- [ ] Ask question requiring multiple sections
- [ ] Verify citations are accurate
- [ ] Test error cases (invalid URL, network error)

---

## Debugging Tips

### Vector DB Issues
```bash
# Check Chroma logs
docker-compose logs chroma

# Restart Chroma
docker-compose restart chroma

# Reset Chroma data (⚠️ deletes all data)
rm -rf chroma_data && docker-compose up -d
```

### LMStudio Issues
- Ensure server is running: http://localhost:1234/v1/models
- Check model is loaded in LMStudio UI
- Increase context length in LMStudio settings
- Try different models if responses are poor

### Embedding Issues
```python
# Test embedding generation
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("test sentence")
print(f"Embedding shape: {embedding.shape}")  # Should be (384,)
```

### Import Issues
```python
# Ensure src is in Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

---

## Performance Optimization

### Embedding Generation
```python
# Batch processing is 10x faster
embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)

# Use GPU if available
model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
```

### Vector Search
```python
# Limit results for faster queries
results = vector_db.search(query_embedding, k=5)  # Top 5 only

# Use filters to narrow search
results = vector_db.search(
    query_embedding,
    k=5,
    filter={"section": "History"}
)
```

### Chunking
```python
# Experiment with chunk sizes
# Smaller chunks = more precise, but less context
# Larger chunks = more context, but less precise

CHUNK_SIZE = 800  # tokens
CHUNK_OVERLAP = 150  # tokens
```

---

## Common Pitfalls

### 1. Token Limits
**Problem**: LLM crashes with context too large

**Solution**: 
- Reduce `TOP_K_RESULTS` in .env
- Implement context truncation
- Use smaller chunk sizes

### 2. Poor Retrieval
**Problem**: Irrelevant chunks retrieved

**Solution**:
- Improve chunking strategy (semantic boundaries)
- Increase `TOP_K_RESULTS` 
- Add query reformulation
- Try different embedding models

### 3. Citation Errors
**Problem**: Citations point to wrong sections

**Solution**:
- Preserve metadata during chunking
- Validate metadata in tests
- Post-process LLM output for citation format

### 4. Slow Indexing
**Problem**: Takes > 1 minute to index page

**Solution**:
- Use batch embedding generation
- Increase `batch_size` in embedding config
- Consider async processing

---

## Code Style Guide

### Type Hints
```python
from typing import List, Dict, Optional

def process_document(text: str, chunk_size: int = 800) -> List[Dict[str, str]]:
    """Process document into chunks."""
    pass
```

### Docstrings
```python
def similarity_search(query: str, k: int = 5) -> List[Document]:
    """
    Search for similar documents.
    
    Args:
        query: Search query text
        k: Number of results to return
        
    Returns:
        List of Document objects sorted by relevance
        
    Raises:
        VectorDBError: If database connection fails
    """
    pass
```

### Error Handling
```python
try:
    result = scraper.fetch(page_title)
except NetworkError as e:
    logger.error(f"Failed to fetch page: {e}")
    raise UserFacingError("Could not load Wikipedia page. Check your internet connection.")
```

---

## Environment Variables Reference

### Required for MVP
```bash
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
VECTOR_DB=chroma
CHROMA_HOST=localhost
```

### Optional with Defaults
```bash
CHUNK_SIZE=800
CHUNK_OVERLAP=150
TOP_K_RESULTS=5
EMBEDDING_MODEL=all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

### Future (Cloud Migration)
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

---

## Git Workflow

### Initial Commit
```bash
git init
git add .
git commit -m "Initial commit: Project structure and roadmap"
```

### Feature Development
```bash
git checkout -b feature/wikipedia-scraper
# ... develop ...
git add src/services/wikipedia_scraper.py tests/test_wikipedia_scraper.py
git commit -m "feat: Implement Wikipedia scraper with API integration"
git checkout main
git merge feature/wikipedia-scraper
```

### Commit Message Convention
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code restructuring
- `test:` Test additions
- `chore:` Maintenance tasks

---

## IDE Configuration (VS Code)

### Recommended Extensions
- Python (Microsoft)
- Pylance
- Ruff
- Python Docstring Generator
- Docker

### Settings (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true
}
```

---

## Resource Links

### Documentation
- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [LMStudio](https://lmstudio.ai/docs)

### Learning Resources
- [RAG Tutorial](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [Vector Database Comparison](https://vdbs.superlinked.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

### Community
- [LangChain Discord](https://discord.gg/langchain)
- [ChromaDB Discord](https://discord.gg/MMeYNTmh3x)

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv pip install -e ".[dev]"

# Or sync dependencies
uv pip sync
```

### "Connection refused" (Chroma)
```bash
# Check Docker is running
docker ps

# Restart Chroma
docker-compose restart chroma
```

### "Model not found" (LMStudio)
- Verify model is loaded in LMStudio UI
- Check model name matches .env configuration
- Try hitting "Start Server" again

### Slow responses
- Reduce `CHUNK_SIZE` and `TOP_K_RESULTS`
- Use smaller/faster LLM model
- Enable GPU for embeddings if available

---

## Next Steps After MVP

Once you have a working MVP, consider:

1. **Web Interface**: Build FastAPI backend + React frontend
2. **Multi-document**: Index multiple Wikipedia pages, search across all
3. **Caching**: Add Redis for query result caching
4. **Monitoring**: Add Prometheus metrics, Grafana dashboards
5. **Cloud Deployment**: Deploy to AWS/GCP with managed services
6. **Browser MCP**: Integrate browser automation for data retrieval
7. **Fine-tuning**: Train custom embedding model on Wikipedia
8. **Advanced RAG**: Implement query reformulation, hypothetical document embeddings

---

**Happy Building! 🚀**
