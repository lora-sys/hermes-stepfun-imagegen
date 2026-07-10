# Contributing to Hermes StepFun ImageGen

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Be respectful and constructive. We're all here to learn and build together.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/lora-sys/hermes-stepfun-imagegen/issues) to avoid duplicates
2. Create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Hermes version, Python version, OS)
   - Relevant log snippets

### Suggesting Features

1. Open an issue with the tag `enhancement`
2. Describe the use case and expected behavior
3. If possible, suggest an implementation approach

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass:
   ```bash
   python -m pytest tests/
   ```
6. Commit with a clear message:
   ```bash
   git commit -m "feat: add support for XYZ"
   ```
7. Push to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```
8. Open a Pull Request against `main`

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- A StepFun API key for testing

### Setup

```bash
# Clone the repo
git clone https://github.com/lora-sys/hermes-stepfun-imagegen.git
cd hermes-stepfun-imagegen

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .

# Install dev dependencies
pip install pytest pytest-cov black ruff
```

### Project Structure

```
hermes-stepfun-imagegen/
├── src/
│   └── hermes_stepfun_imagegen/
│       ├── __init__.py      # Plugin implementation
│       └── plugin.yaml      # Plugin manifest
├── tests/
│   └── test_stepfun.py      # Unit tests
├── docs/
│   └── assets/              # Screenshots and images
├── pyproject.toml           # Package configuration
├── README.md                # Documentation
└── CONTRIBUTING.md          # This file
```

### Plugin Architecture

The plugin follows the Hermes `ImageGenProvider` ABC:

- `generate()` - Main entry point for image generation
- `list_models()` - Returns available models
- `capabilities()` - Declares supported modalities
- `is_available()` - Checks if API key is configured

See the [Image Generation Provider Plugin docs](https://hermes-agent.nousresearch.com/docs/developer-guide/image-gen-provider-plugin) for details.

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=hermes_stepfun_imagegen tests/

# Run specific test
python -m pytest tests/test_stepfun.py::test_text_to_image -v
```

### Code Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `black` for formatting:
  ```bash
  black src/ tests/
  ```
- Use `ruff` for linting:
  ```bash
  ruff check src/ tests/
  ```

## Release Process

Releases are automated via GitHub Actions. When a new tag is pushed, the workflow will:

1. Run tests
2. Build the package
3. Publish to PyPI
4. Create a GitHub Release

To create a new release:

```bash
# Update version in pyproject.toml
git add -A
git commit -m "chore: release v0.2.0"
git tag v0.2.0
git push --tags
```

## Questions?

Feel free to open an issue or reach out on the [Nous Research Discord](https://discord.gg/nousresearch) in `#plugins-skills-and-skins`.
