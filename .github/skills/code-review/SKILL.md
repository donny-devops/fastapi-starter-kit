---
name: code-review
description: Comprehensive code review guidelines for Python and FastAPI pull requests.
---

# Code Review Skill

## Overview
Perform thorough, constructive code reviews focusing on security, code quality, test coverage, and FastAPI best practices.

## Guidelines

### 1. Security & Authentication
- Ensure endpoints requiring authentication use appropriate dependencies.
- Verify sensitive configuration values are loaded via environment variables or Pydantic settings, never hardcoded.
- Validate all incoming payload types using Pydantic schemas to prevent injection attacks.

### 2. FastAPI & Python Best Practices
- Check that asynchronous functions (`async def`) are used appropriately for non-blocking I/O operations.
- Ensure type hints are accurate and fully defined across function parameters and return types.
- Verify proper exception handling using standard HTTP exceptions (`HTTPException`).

### 3. Code Quality & Maintainability
- Keep controller logic thin by pushing business logic into service or utility layers.
- Check for duplicate logic or missed opportunities for modularity.
- Ensure formatting and style adhere to PEP 8 standards.

### 4. Testing
- Verify new features or bug fixes include corresponding unit or integration tests.
- Ensure existing test suites pass cleanly.

## Review Output Format
When providing review feedback, structure findings as follows:
- **Summary**: High-level review overview.
- **Critical/Blocking Issues**: Security risks, bugs, or breaking changes.
- **Suggestions**: Refactoring, readability improvements, or non-blocking enhancements.
- **Positives**: Notable well-implemented design choices.
