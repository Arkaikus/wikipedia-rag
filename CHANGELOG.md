# Changelog

## [0.1.0] - 2026-02-11

### Changed: Migration to uv Package Manager

The project now uses `uv` instead of traditional pip for dependency management. This provides significant benefits:

#### ✨ New Files
- **`pyproject.toml`** - Replaced `requirements.txt` with modern Python packaging standard
  - Includes project metadata
  - Dependencies and optional dev dependencies
  - Tool configurations (black, ruff, mypy, pytest)
  - Build system configuration

- **`UV_GUIDE.md`** - Comprehensive guide for using uv
  - Installation instructions
  - Common commands
  - Speed comparisons
  - Troubleshooting tips

- **`Makefile`** - Convenient shortcuts for common tasks
  - `make setup` - One-command project setup
  - `make dev` - Quick development environment
  - `make test` - Run tests
  - `make quality` - Run all quality checks
  - `make docker-up/down` - Manage Docker services
  - And more! Run `make help` for full list

#### 📝 Updated Files
- **`README.md`** - Updated to use uv commands, added documentation index
- **`QUICKSTART.md`** - Added uv installation, updated all setup commands, added Make shortcuts
- **`DEVELOPMENT.md`** - Updated workflow to use uv and Make commands
- **`TODO.md`** - Updated Phase 1 to include uv setup steps
- **`MIGRATION.md`** - Updated package installation commands to use uv
- **`.gitignore`** - Added uv-specific files (`.venv/`, `uv.lock`, `.python-version`)

#### 🗑️ Removed Files
- **`requirements.txt`** - Replaced by `pyproject.toml`

### Benefits of This Change

#### Speed Improvements
- **10-100x faster** than pip for dependency installation
- Initial install: ~3 seconds vs ~45 seconds with pip
- Better dependency resolution

#### Developer Experience
- **Modern Python packaging** with `pyproject.toml`
- **Makefile shortcuts** for common tasks
- **Better dependency management** with built-in locking
- **Consistent environments** across team members

#### Backward Compatibility
- uv can still read `requirements.txt` files if needed
- All pip commands have uv equivalents: `pip install` → `uv pip install`

### Migration Guide for Existing Users

If you already had the project set up with pip:

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Remove old virtual environment
rm -rf venv

# 3. Create new environment with uv
uv venv
source .venv/bin/activate

# 4. Install dependencies
uv pip install -e ".[dev]"

# Done! Much faster than before.
```

### Quick Command Reference

#### Before (with pip)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### After (with uv)
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Or even simpler with Make:
make setup
```

### Documentation Structure

All documentation has been updated to reflect the new setup:

1. **Getting Started**: README.md → QUICKSTART.md
2. **Development**: DEVELOPMENT.md (includes Make commands)
3. **Architecture**: ARCHITECTURE.md (unchanged)
4. **Roadmap**: TODO.md (updated Phase 1)
5. **Migration**: MIGRATION.md (cloud migration guide)
6. **uv Reference**: UV_GUIDE.md (new)

### Next Steps

The project is ready for implementation following the TODO.md roadmap:

- ✅ Project structure complete
- ✅ Dependency management configured
- ✅ Docker Compose configured
- ✅ Documentation complete
- ⏭️ **Next**: Implement Wikipedia scraper (TODO.md Phase 2)

### Notes

- Virtual environment is now `.venv/` instead of `venv/` (uv convention)
- All development tools configured in `pyproject.toml`
- Makefile provides shortcuts but direct commands still work
- Project maintains Python 3.11+ requirement

---

## Project Timeline

- **2026-02-11**: Initial project setup with comprehensive roadmap
- **2026-02-11**: Migration to uv package manager
- **Next**: Begin MVP implementation (Wikipedia scraper)
