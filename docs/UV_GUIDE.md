# uv Quick Reference Guide

`uv` is a blazingly fast Python package installer and resolver written in Rust by Astral (makers of Ruff). It's 10-100x faster than pip!

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# macOS with Homebrew
brew install uv

# With pip (any platform)
pip install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Common Commands for This Project

### Initial Setup
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install project with all dependencies (including dev)
uv pip install -e ".[dev]"

# Install without dev dependencies
uv pip install -e .
```

### Adding New Dependencies

```bash
# Add a new package to pyproject.toml manually, then:
uv pip install -e ".[dev]"

# Or install directly (though you'll need to add to pyproject.toml manually)
uv pip install package-name
```

### Update Dependencies

```bash
# Update all dependencies to latest compatible versions
uv pip install --upgrade -e ".[dev]"

# Update specific package
uv pip install --upgrade package-name
```

### List Dependencies

```bash
# List installed packages
uv pip list

# Show dependency tree
uv pip freeze
```

### Uninstall Package

```bash
uv pip uninstall package-name
```

### Sync Dependencies

```bash
# Ensure installed packages match pyproject.toml exactly
uv pip sync
```

## Why uv?

### Speed Comparison
- **pip**: ~45 seconds to install all dependencies
- **uv**: ~3 seconds to install all dependencies (15x faster!)

### Benefits
- ✅ **10-100x faster** than pip
- ✅ **Better dependency resolution** - catches conflicts faster
- ✅ **Drop-in replacement** - works with existing requirements.txt and pyproject.toml
- ✅ **No need for pip-tools** - built-in locking and syncing
- ✅ **Cross-platform** - works on macOS, Linux, Windows

### uv vs Poetry vs pip

| Feature | uv | Poetry | pip |
|---------|-------|--------|-----|
| Speed | ⚡⚡⚡ | ⚡ | ⚡ |
| Dependency Resolution | ✅ | ✅ | ⚠️ |
| Lock Files | ✅ | ✅ | ❌ |
| Learning Curve | Low | Medium | Low |
| pyproject.toml | ✅ | ✅ | ⚠️ |

## Advanced Usage

### Create venv with specific Python version
```bash
uv venv --python 3.11
uv venv --python 3.12
```

### Install from requirements.txt (compatibility)
```bash
uv pip install -r requirements.txt
```

### Compile dependencies (like pip-compile)
```bash
uv pip compile pyproject.toml -o requirements.txt
```

### Create reproducible builds
```bash
# Generate lock file
uv pip freeze > requirements.lock

# Install from lock file
uv pip install -r requirements.lock
```

## Project-Specific Workflows

### Fresh Start
```bash
# Remove old environment
rm -rf .venv

# Create new environment and install
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Before Committing
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest
```

### Adding a New Feature Dependency

1. Edit `pyproject.toml`:
```toml
[project]
dependencies = [
    # ... existing deps
    "new-package>=1.0.0",
]
```

2. Install:
```bash
uv pip install -e ".[dev]"
```

### Adding a New Dev Dependency

1. Edit `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
    # ... existing dev deps
    "new-dev-tool>=2.0.0",
]
```

2. Install:
```bash
uv pip install -e ".[dev]"
```

## Troubleshooting

### "uv: command not found"
```bash
# Add uv to PATH (usually automatic after install)
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Virtual environment not activating
```bash
# Make sure you're in project root
cd /Users/santiago/Documents/rag-example

# Create venv
uv venv

# Activate (use the right command for your shell)
source .venv/bin/activate
```

### Dependency conflicts
```bash
# uv will show you conflicts clearly
# Fix conflicts in pyproject.toml, then:
uv pip install -e ".[dev]"
```

### Slow first install
```bash
# First install needs to download packages
# Subsequent installs use cache and are blazing fast
# To see cache location:
uv cache dir
```

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [pyproject.toml Spec](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [uv vs pip Benchmarks](https://github.com/astral-sh/uv?tab=readme-ov-file#highlights)

## Migration from pip

If you're used to pip, here's the translation:

| pip command | uv command |
|-------------|------------|
| `pip install package` | `uv pip install package` |
| `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| `pip install -e .` | `uv pip install -e .` |
| `pip list` | `uv pip list` |
| `pip freeze` | `uv pip freeze` |
| `pip uninstall package` | `uv pip uninstall package` |
| `python -m venv venv` | `uv venv` |

**Key Difference**: uv is much faster and has better dependency resolution! 🚀
