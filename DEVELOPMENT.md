# Development Guide

This guide covers the development workflow for the MCH-Extract package, including setup, testing, building, and publishing.

## Prerequisites

- **uv**: Modern Python package manager (recommended)
- **Python 3.10+**: Required for the project
- **Git**: For version control

## Quick Setup

```bash
# Clone the repository
git clone https://github.com/mspoto/mch-extract.git
cd mch-extract

# Install all dependencies including development tools
uv sync --extra dev

# Install pre-commit hooks (recommended)
uv run pre-commit install
```

## Development Commands

### Environment Setup

#### Install Development Dependencies
```bash
uv sync --extra dev
```

This installs all dependencies including development tools:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `ruff` - Linting and formatting
- `mypy` - Type checking
- `pre-commit` - Git hooks for automated quality checks

#### Install Pre-commit Hooks (Recommended)
```bash
uv run pre-commit install
```

This sets up automated quality checks that run before each commit:
- **Ruff linting** with auto-fix
- **Ruff formatting**
- **MyPy type checking**
- **Pytest testing**

With pre-commit installed, these checks run automatically on `git commit`. You can also run them manually:
```bash
# Run all pre-commit hooks on all files
uv run pre-commit run --all-files

# Run pre-commit hooks on staged files only
uv run pre-commit run
```

### Manual Testing (When Needed)

#### Run Tests with Coverage
```bash
# Terminal coverage report
uv run pytest tests/ --cov=mchextract --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ --cov=mchextract --cov-report=html
# View at htmlcov/index.html
```

#### Run Specific Tests
```bash
# Run specific test file
uv run pytest tests/test_basic.py -v

# Run tests matching pattern
uv run pytest -k "test_import" -v
```

### Building and Publishing

#### Build Package
```bash
uv build
```

This creates both source distribution (`.tar.gz`) and wheel (`.whl`) in the `dist/` directory.

#### Check Package
```bash
# Install twine if needed
uv add --dev twine

# Check package metadata and structure
uv run twine check dist/*
```

#### Clean Build Artifacts
```bash
rm -rf dist/
rm -rf build/
rm -rf *.egg-info/
rm -rf .pytest_cache/
rm -rf htmlcov/
rm -rf .coverage
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
```

#### Version Management
```bash
# Bump patch version (0.1.0 -> 0.1.1)
uv version --bump patch

# Bump minor version (0.1.0 -> 0.2.0)
uv version --bump minor

# Bump major version (0.1.0 -> 1.0.0)
uv version --bump major

# Set specific version
uv version 1.0.0

# Preview version change without applying
uv version --bump patch --dry-run
```

#### Publishing to PyPI

##### Test PyPI (Recommended for testing)
```bash
# Build and publish to test PyPI
uv build
uv publish --index testpipy
```

##### Production PyPI
```bash
# Build and publish to PyPI
uv build
uv publish
```

**Note**: You'll need to configure PyPI credentials. See [Authentication](#authentication) section below.

### Simplified Development Workflow

With pre-commit hooks installed, your workflow becomes much simpler:

```bash
# 1. Install dependencies and pre-commit hooks (one-time setup)
uv sync --extra dev
uv run pre-commit install

# 2. Make your changes to the code

# 3. Commit your changes (pre-commit runs automatically)
git add .
git commit -m "Your commit message"
# Pre-commit will automatically:
# - Format your code with ruff
# - Fix linting issues with ruff
# - Run type checking with mypy  
# - Run all tests with pytest

# 4. If pre-commit passes, push your changes
git push

# 5. If you need to build the package
uv build
```

**Note**: If pre-commit finds issues, fix them and commit again. The hooks ensure code quality before each commit.

## Authentication

### PyPI Authentication

For publishing to PyPI, you have several options:

#### Option 1: API Token (Recommended)
1. Create an API token at https://pypi.org/manage/account/token/
2. Set environment variable:
   ```bash
   export UV_PUBLISH_PASSWORD=your-api-token
   export UV_PUBLISH_USERNAME=__token__
   ```

#### Option 2: Trusted Publishing (GitHub Actions)
For automated publishing from GitHub Actions, set up trusted publishing:
1. Go to https://pypi.org/manage/project/mch-extract/settings/publishing/
2. Add GitHub repository as trusted publisher
3. No credentials needed in GitHub Actions

## Continuous Integration

The project uses GitHub Actions for CI/CD:

- **`.github/workflows/ci.yml`**: Runs tests, linting, and builds on every push/PR
- **`.github/workflows/publish.yml`**: Publishes to PyPI on releases

### Local CI Simulation
Pre-commit hooks automatically run the same checks as CI. To manually run all checks:

```bash
# Run all pre-commit hooks (same as CI checks)
uv run pre-commit run --all-files

# Or run individual tools if needed
uv run ruff check mchextract tests
uv run ruff format --check mchextract tests  
uv run mypy mchextract
uv run pytest tests/ --cov=mchextract
uv build
```

## Project Structure

```
mch-extract/
├── mchextract/              # Main package directory
│   ├── __init__.py         # Package initialization and exports
│   ├── api.py              # Main API classes
│   ├── cli.py              # Command-line interface
│   ├── models.py           # Data models and enums
│   └── ...                 # Other modules
├── tests/                  # Test directory
│   ├── __init__.py
│   ├── test_basic.py       # Basic functionality tests
│   └── ...                 # Additional test files
├── .github/workflows/      # GitHub Actions CI/CD
├── dist/                   # Built packages (created by uv build)
├── pyproject.toml          # Project configuration
├── uv.lock                 # Dependency lock file
├── README.md               # User documentation
└── DEVELOPMENT.md          # This file
```

## Configuration Files

### pyproject.toml
Main configuration file containing:
- Project metadata and dependencies
- Build system configuration
- Tool configurations (ruff, mypy, pytest)

### uv.lock
Dependency lock file ensuring reproducible builds across environments.

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Make sure package is installed in development mode
uv sync
```

#### Pre-commit Issues
```bash
# If pre-commit hooks fail, you can run them manually to see details
uv run pre-commit run --all-files

# Update pre-commit hooks to latest versions
uv run pre-commit autoupdate
```

#### Test Failures
```bash
# Run tests with verbose output to see detailed errors
uv run pytest tests/ -v -s

# Run a specific test for debugging
uv run pytest tests/test_basic.py::test_import -v -s
```

#### Build Failures
```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Rebuild
uv build
```

#### Linting/Formatting Errors
```bash
# Pre-commit handles these automatically, but if you need manual control:
uv run ruff check mchextract tests --fix
uv run ruff format mchextract tests
```

### Getting Help

- **uv documentation**: https://docs.astral.sh/uv/
- **ruff documentation**: https://docs.astral.sh/ruff/
- **pytest documentation**: https://docs.pytest.org/
- **Project issues**: https://github.com/mspoto/mch-extract/issues

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Install development environment: `uv sync --extra dev && uv run pre-commit install`
4. Make your changes
5. Commit your changes: `git commit -m "Description"` (pre-commit runs automatically)
6. Push to your fork: `git push origin feature-name`
7. Create a Pull Request

## Release Process

1. Update version: `uv version --bump minor`
2. Update CHANGELOG.md with release notes
3. Commit changes: `git commit -m "Release v0.2.0"`
4. Tag release: `git tag v0.2.0`
5. Push: `git push && git push --tags`
6. Create GitHub release (triggers automatic PyPI publishing)

## Best Practices

- **Use pre-commit hooks**: `uv run pre-commit install` (automates code quality)
- **Let pre-commit handle formatting and linting**: No need to run manual commands
- **Write tests for new features**: Add tests in `tests/` directory
- **Keep dependencies up to date**: `uv sync --upgrade`
- **Update documentation**: Keep README.md and docstrings current
- **Use semantic versioning**: Major.Minor.Patch (e.g., 1.2.3)
- **Run coverage reports when needed**: `uv run pytest tests/ --cov=mchextract`
