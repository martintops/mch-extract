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

#### Install Package in Development Mode
```bash
uv sync
```

This installs the package in editable mode so changes are immediately available.

### Code Quality

#### Linting
```bash
# Check for linting issues
uv run ruff check mchextract tests

# Auto-fix issues where possible
uv run ruff check --fix mchextract tests
```

#### Formatting
```bash
# Format code
uv run ruff format mchextract tests

# Check formatting without making changes
uv run ruff format --check mchextract tests
```

#### Type Checking
```bash
uv run mypy mchextract
```

### Testing

#### Run All Tests
```bash
uv run pytest tests/ -v
```

#### Run Tests with Coverage
```bash
# Terminal coverage report
uv run pytest tests/ --cov=mchextract --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ --cov=mchextract --cov-report=html
# View at htmlcov/index.html
```

#### Run Specific Test File
```bash
uv run pytest tests/test_basic.py -v
```

#### Run Tests Matching Pattern
```bash
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

### Complete Development Workflow

Here's a typical development workflow combining all the tools:

```bash
# 1. Install dependencies
uv sync --extra dev

# 2. Make your changes to the code

# 3. Format code
uv run ruff format mchextract tests

# 4. Fix linting issues
uv run ruff check --fix mchextract tests

# 5. Check types
uv run mypy mchextract

# 6. Run tests
uv run pytest tests/ --cov=mchextract

# 7. Build package to test
uv build

# 8. If everything looks good, commit and push
git add .
git commit -m "Your commit message"
git push
```

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
To simulate what CI does locally:

```bash
# Run the same checks as CI
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

#### Linting Errors
```bash
# See all issues
uv run ruff check mchextract tests

# Auto-fix what can be fixed
uv run ruff check --fix mchextract tests

# Format code
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
3. Make your changes
4. Run the development workflow commands above
5. Commit your changes: `git commit -m "Description"`
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

- **Always run tests before committing**: `uv run pytest`
- **Format code consistently**: `uv run ruff format mchextract tests`
- **Fix linting issues**: `uv run ruff check --fix mchextract tests`
- **Keep dependencies up to date**: `uv sync --upgrade`
- **Write tests for new features**: Add tests in `tests/` directory
- **Update documentation**: Keep README.md and docstrings current
- **Use semantic versioning**: Major.Minor.Patch (e.g., 1.2.3)
