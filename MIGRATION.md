# Cloud Migration Guide

Guide for migrating your RAG Wikipedia Chatbot from local (LMStudio) to cloud services.

---

## Overview

The adapter pattern design allows seamless migration from local to cloud with minimal code changes:

**Local Setup (MVP)**:
- LLM: LMStudio (local)
- Vector DB: Chroma (Docker)
- Embeddings: sentence-transformers (local)

**Cloud Setup (Production)**:
- LLM: OpenAI/Azure OpenAI/Anthropic
- Vector DB: Chroma Cloud/Pinecone/Weaviate Cloud
- Embeddings: OpenAI/Cohere

---

## Migration Scenarios

### Scenario 1: LMStudio → OpenAI (Easiest)

**Why**: Fastest migration, best performance, pay-as-you-go

**Steps**:

1. **Get OpenAI API Key**
   ```bash
   # Visit: https://platform.openai.com/api-keys
   # Create new secret key
   ```

2. **Update `.env`**
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-proj-...
   OPENAI_MODEL=gpt-4-turbo-preview
   ```

3. **Restart application**
   ```bash
   python main.py
   # Should now use OpenAI automatically
   ```

**Cost Estimate** (GPT-4 Turbo):
- Input: $10 / 1M tokens
- Output: $30 / 1M tokens
- Typical query: ~2000 input + 500 output = $0.035
- 1000 queries/month ≈ $35/month

**Advantages**:
- ✅ Better response quality
- ✅ Faster responses
- ✅ No local GPU needed
- ✅ Latest models

**Disadvantages**:
- ❌ Costs money
- ❌ Data sent to OpenAI
- ❌ Requires internet

---

### Scenario 2: LMStudio → Azure OpenAI (Enterprise)

**Why**: Enterprise compliance, data privacy, SLA guarantees

**Steps**:

1. **Create Azure OpenAI Resource**
   - Azure Portal → Create Resource → Azure OpenAI
   - Choose region (e.g., East US)
   - Deploy model (gpt-4, gpt-35-turbo)

2. **Get Credentials**
   ```bash
   # From Azure Portal:
   ENDPOINT: https://your-resource.openai.azure.com/
   API_KEY: ...
   DEPLOYMENT_NAME: gpt-4
   ```

3. **Update `.env`**
   ```bash
   LLM_PROVIDER=azure
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_KEY=...
   AZURE_OPENAI_DEPLOYMENT=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

4. **Implement Azure Adapter** (if not already done)
   ```python
   # src/adapters/azure_openai_adapter.py
   from openai import AzureOpenAI
   
   class AzureOpenAIAdapter(LLMAdapter):
       def __init__(self):
           self.client = AzureOpenAI(
               api_key=os.getenv("AZURE_OPENAI_KEY"),
               api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
               azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
           )
   ```

**Advantages**:
- ✅ Enterprise SLA
- ✅ Data stays in your tenant
- ✅ Compliance (HIPAA, SOC 2)
- ✅ Private network support

**Disadvantages**:
- ❌ More expensive than OpenAI
- ❌ Setup complexity
- ❌ Model availability varies by region

---

### Scenario 3: Chroma (Docker) → Chroma Cloud (Managed)

**Why**: No infrastructure management, auto-scaling

**Steps**:

1. **Sign up for Chroma Cloud**
   ```bash
   # Visit: https://trychroma.com/
   # Create account and workspace
   ```

2. **Get credentials**
   ```bash
   # From Chroma dashboard:
   API_URL: https://api.trychroma.com
   API_KEY: ...
   ```

3. **Update `.env`**
   ```bash
   VECTOR_DB=chroma_cloud
   CHROMA_CLOUD_URL=https://api.trychroma.com
   CHROMA_CLOUD_API_KEY=...
   ```

4. **Update adapter**
   ```python
   # src/adapters/chroma_adapter.py
   import chromadb
   from chromadb.config import Settings
   
   if os.getenv("VECTOR_DB") == "chroma_cloud":
       self.client = chromadb.HttpClient(
           host=os.getenv("CHROMA_CLOUD_URL"),
           headers={"Authorization": f"Bearer {os.getenv('CHROMA_CLOUD_API_KEY')}"}
       )
   ```

5. **Migrate data** (if needed)
   ```bash
   # Export from local Chroma
   python scripts/export_chroma.py

   # Import to Chroma Cloud
   python scripts/import_chroma.py --target cloud
   ```

**Advantages**:
- ✅ Zero ops overhead
- ✅ Auto-scaling
- ✅ High availability
- ✅ Built-in backups

**Disadvantages**:
- ❌ Costs
- ❌ Data leaves your infrastructure
- ❌ Less customization

---

### Scenario 4: Chroma → Pinecone (Specialized Vector DB)

**Why**: Optimized for vector search, excellent performance

**Steps**:

1. **Create Pinecone account**
   ```bash
   # Visit: https://www.pinecone.io/
   # Create index with dimension=384 (for all-MiniLM-L6-v2)
   ```

2. **Install Pinecone client**
   ```bash
   uv pip install pinecone-client
   ```

3. **Update `.env`**
   ```bash
   VECTOR_DB=pinecone
   PINECONE_API_KEY=...
   PINECONE_ENVIRONMENT=us-east1-gcp
   PINECONE_INDEX_NAME=wikipedia-rag
   ```

4. **Implement Pinecone adapter**
   ```python
   # src/adapters/pinecone_adapter.py
   import pinecone
   
   class PineconeAdapter(VectorDBAdapter):
       def __init__(self):
           pinecone.init(
               api_key=os.getenv("PINECONE_API_KEY"),
               environment=os.getenv("PINECONE_ENVIRONMENT")
           )
           self.index = pinecone.Index(os.getenv("PINECONE_INDEX_NAME"))
   ```

**Pricing**:
- Starter: Free (1M vectors, 1 pod)
- Standard: ~$70/month per pod
- Enterprise: Custom pricing

**Advantages**:
- ✅ Purpose-built for vectors
- ✅ Excellent performance
- ✅ Generous free tier
- ✅ Great documentation

**Disadvantages**:
- ❌ Another service to manage
- ❌ More expensive than Chroma
- ❌ Vendor lock-in

---

## Hybrid Approach (Recommended for Production)

Mix local and cloud for cost optimization:

**Configuration**:
```python
# .env
LLM_PROVIDER=conditional  # New option

# Conditional logic
LLM_PROVIDER_SIMPLE=lmstudio  # For simple queries
LLM_PROVIDER_COMPLEX=openai   # For complex queries

# Thresholds
COMPLEXITY_THRESHOLD=0.7
QUERY_LENGTH_THRESHOLD=100
```

**Implementation**:
```python
def choose_llm_provider(query: str) -> str:
    """Route queries based on complexity."""
    if len(query) > 100 or detect_complexity(query) > 0.7:
        return "openai"  # Use cloud for complex
    return "lmstudio"  # Use local for simple
```

**Benefits**:
- Save costs on simple queries (local)
- Better quality on complex queries (cloud)
- Fallback if one provider fails

---

## Complete Migration Path

### Phase 1: Local Only (MVP)
- LLM: LMStudio
- Vector DB: Chroma (Docker)
- Embeddings: sentence-transformers
- **Cost**: $0/month
- **Setup time**: 1 hour

### Phase 2: Hybrid (Optimization)
- LLM: LMStudio (simple) + OpenAI (complex)
- Vector DB: Chroma (Docker)
- Embeddings: sentence-transformers
- **Cost**: $10-50/month
- **Migration time**: 2 hours

### Phase 3: Partial Cloud (Scaling)
- LLM: OpenAI/Azure
- Vector DB: Chroma (Docker)
- Embeddings: sentence-transformers
- **Cost**: $50-200/month
- **Migration time**: 4 hours

### Phase 4: Full Cloud (Production)
- LLM: Azure OpenAI (enterprise)
- Vector DB: Pinecone/Chroma Cloud
- Embeddings: OpenAI embeddings
- **Cost**: $200-1000/month
- **Migration time**: 1-2 days

---

## Cost Comparison

### Local (MVP)
- **Infrastructure**: $0
- **Compute**: Your hardware
- **Total**: $0/month
- **Queries**: Unlimited (limited by hardware)

### Hybrid
- **LMStudio**: $0
- **OpenAI**: $30/month (1000 complex queries)
- **Chroma**: $0 (Docker)
- **Total**: $30/month

### Full Cloud (OpenAI + Pinecone)
- **OpenAI**: $100/month (3000 queries)
- **Pinecone**: $70/month (starter pod)
- **Hosting**: $50/month (AWS/GCP)
- **Total**: $220/month

### Enterprise (Azure + Managed Services)
- **Azure OpenAI**: $500/month
- **Chroma Cloud**: $200/month
- **Azure Hosting**: $300/month
- **Total**: $1000/month
- **Benefits**: SLA, support, compliance

---

## Migration Checklist

### Pre-Migration
- [ ] Backup current data
- [ ] Document current performance metrics
- [ ] Test cloud adapter in development
- [ ] Estimate costs based on usage patterns
- [ ] Get stakeholder approval for costs

### Migration
- [ ] Set up cloud accounts
- [ ] Configure credentials (use secrets manager)
- [ ] Implement new adapters
- [ ] Update environment configuration
- [ ] Migrate existing data
- [ ] Run integration tests

### Post-Migration
- [ ] Monitor performance (latency, quality)
- [ ] Track costs daily
- [ ] Set up alerts (cost, errors, latency)
- [ ] Optimize queries if costs are high
- [ ] Document new setup

---

## Rollback Plan

If cloud migration causes issues:

1. **Immediate rollback**
   ```bash
   # Revert .env
   LLM_PROVIDER=lmstudio
   VECTOR_DB=chroma
   
   # Restart services
   docker-compose up -d
   # Start LMStudio
   python main.py
   ```

2. **Data recovery**
   ```bash
   # Restore from backup
   docker-compose down
   cp -r chroma_data_backup chroma_data
   docker-compose up -d
   ```

3. **Monitor stability**
   - Check error rates return to baseline
   - Verify query quality
   - Confirm costs return to $0

---

## Best Practices

### 1. Gradual Migration
- Start with 10% of traffic to cloud
- Monitor quality and costs
- Increase gradually if successful

### 2. Cost Controls
- Set budget alerts in cloud provider
- Implement rate limiting
- Cache frequently asked questions
- Use cheaper models for simple queries

### 3. Security
- Use secrets manager (AWS Secrets Manager, Azure Key Vault)
- Never commit API keys to git
- Rotate keys regularly
- Use least-privilege IAM roles

### 4. Monitoring
```python
# Add logging for all LLM calls
logger.info(f"LLM call: provider={provider}, tokens={tokens}, cost=${cost}")

# Track metrics
metrics.increment("llm.calls", tags=["provider:openai"])
metrics.histogram("llm.latency", latency_ms)
metrics.gauge("llm.cost", cost)
```

### 5. Fallbacks
```python
def generate_response(query, context):
    try:
        return openai_adapter.generate(query, context)
    except OpenAIError:
        logger.warning("OpenAI failed, falling back to LMStudio")
        return lmstudio_adapter.generate(query, context)
```

---

## Future: Browser MCP Integration

When using Browser MCP for data retrieval:

**Local**:
- Browser MCP runs on your machine
- No additional costs
- Full control

**Cloud**:
- Use headless browser services (Browserless, ScrapingBee)
- Add to cost estimate: ~$50/month
- Easier scaling

---

## Support & Resources

### Cloud Provider Docs
- [OpenAI Platform](https://platform.openai.com/docs)
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Pinecone Docs](https://docs.pinecone.io/)
- [Chroma Cloud](https://docs.trychroma.com/deployment/cloud)

### Cost Calculators
- [OpenAI Pricing](https://openai.com/pricing)
- [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
- [Pinecone Pricing](https://www.pinecone.io/pricing/)

### Community
- [r/LocalLLaMA](https://reddit.com/r/LocalLLaMA) - Local vs Cloud discussions
- [LangChain Discord](https://discord.gg/langchain) - RAG architectures

---

**Remember**: The adapter pattern makes migration painless. Start local, migrate when ready! 🚀
