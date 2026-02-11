# Quick Start Guide

Get your RAG Wikipedia Chatbot running in under 10 minutes with uv!

## Super Quick Start (Using Make)

If you want the absolute fastest setup:

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Then run setup
make setup

# Edit .env, start LMStudio, then:
make run
```

Done! For detailed step-by-step instructions, continue below.

---

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.11 or higher installed
- [ ] uv package manager installed
- [ ] Docker Desktop installed and running
- [ ] LMStudio downloaded and installed
- [ ] At least 8GB RAM available

## Step-by-Step Setup

### 1. Install uv (1 minute)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew on macOS
brew install uv

# Or with pip
pip install uv

# Verify installation
uv --version
```

### 2. Environment Setup (1 minute)

```bash
# Navigate to project directory
cd /Users/santiago/Documents/rag-example

# Create virtual environment and install dependencies (uv is FAST!)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.11+
```

### 3. Install Dependencies (1 minute - uv is ~10x faster than pip!)

```bash
# Install project with all dependencies
uv pip install -e ".[dev]"

# Verify installation
python -c "import langchain; import chromadb; print('Dependencies OK!')"
```

### 4. Configure Environment (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (defaults work for local setup)
# nano .env  # or use your preferred editor
```

**Default configuration works out of the box!**

### 5. Start Vector Database (2 minutes)

```bash
# Start Chroma in Docker
docker-compose up -d

# Verify it's running
docker-compose ps

# Check health
curl http://localhost:8000/api/v1/heartbeat
# Should return: {"nanosecond heartbeat": ...}
```

### 6. Start LMStudio (2 minutes)

1. **Open LMStudio application**

2. **Download a model** (if you haven't already):
   - Recommended: `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`
   - Or: `TheBloke/Llama-2-7B-Chat-GGUF`
   - Click "Search" → Find model → Download

3. **Load the model**:
   - Click on the model in "My Models"
   - Click "Load Model"

4. **Start local server**:
   - Go to "Local Server" tab
   - Click "Start Server"
   - Default port: 1234
   - Verify green status indicator

5. **Test the server**:
   ```bash
   curl http://localhost:1234/v1/models
   # Should return JSON with model info
   ```

### 7. Run the Chatbot

```bash
# Start the application
python main.py
```

## First Interaction

Once the chatbot starts, try this:

```
> load "Albert Einstein"
Loading Wikipedia page: Albert Einstein...
Fetching content...
Processing 87 chunks...
Generating embeddings...
Storing in vector database...
✓ Indexing complete! Ready to chat.

> chat
Entering chat mode. Type 'exit' to quit, 'info' for page details.

You: What were Einstein's major contributions to physics?