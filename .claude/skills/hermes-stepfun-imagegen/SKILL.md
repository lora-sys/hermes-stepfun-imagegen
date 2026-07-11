```markdown
# hermes-stepfun-imagegen Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill provides guidance on contributing to the `hermes-stepfun-imagegen` Python codebase. It documents the repository's coding conventions, commit patterns, and testing strategies, enabling developers to write consistent, high-quality code. While no specific frameworks or automated workflows were detected, this guide covers the project's unique practices and offers command suggestions for common tasks.

## Coding Conventions

### File Naming
- Use **camelCase** for Python files.
  - Example: `imageGen.py`, `stepFunProcessor.py`

### Import Style
- Prefer **relative imports** within the package.
  - Example:
    ```python
    from .utils import processImage
    ```

### Export Style
- Use **named exports**; explicitly define what is exported from each module.
  - Example:
    ```python
    __all__ = ['processImage', 'generateStepFun']
    ```

### Commit Messages
- Follow **Conventional Commits** with the `feat` prefix for new features.
  - Example:
    ```
    feat: add step function for image transformation
    ```

## Workflows

### Adding a New Feature
**Trigger:** When implementing a new capability or function  
**Command:** `/add-feature`

1. Create a new camelCase Python file if needed.
2. Implement the feature using relative imports for dependencies.
3. Add named exports to the module via `__all__`.
4. Write or update corresponding test files (`*.test.*`).
5. Commit changes with a `feat:` prefix and a descriptive message.

### Running Tests
**Trigger:** After making changes or before submitting a pull request  
**Command:** `/run-tests`

1. Locate all test files matching the `*.test.*` pattern.
2. Run the tests using your preferred Python test runner (e.g., `pytest`, `unittest`).
   - Example:
     ```
     pytest
     ```
3. Review test output and fix any failures.

### Importing Utilities
**Trigger:** When reusing code across modules  
**Command:** `/import-utility`

1. Use relative imports to bring in utility functions.
   - Example:
     ```python
     from .utils import helperFunction
     ```

## Testing Patterns

- Test files use the `*.test.*` naming convention (e.g., `imageGen.test.py`).
- The specific testing framework is not enforced; choose a standard Python test runner (such as `pytest` or `unittest`).
- Place tests alongside or near the code they validate.
- Example test file structure:
  ```python
  # imageGen.test.py
  from .imageGen import processImage

  def test_process_image():
      result = processImage('input.png')
      assert result is not None
  ```

## Commands
| Command        | Purpose                                      |
|----------------|----------------------------------------------|
| /add-feature   | Scaffold and commit a new feature            |
| /run-tests     | Run all test files in the repository         |
| /import-utility| Import a utility function via relative import|
```
