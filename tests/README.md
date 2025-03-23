# ModelForge Test Suite

This directory contains tests for the ModelForge project.

## Test Structure

- `conftest.py`: Global test fixtures and configuration
- `data_discovery/`: Tests for the data discovery module
  - `conftest.py`: Shared fixtures for data discovery tests
  - `connectors/`: Tests for individual data connectors
  - `storage/`: Tests for storage implementations
  - `test_catalog.py`: Tests for the dataset catalog
  - `test_discovery_service.py`: Tests for the discovery service
  - `test_models.py`: Tests for data models

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/data_discovery/test_models.py
```

To run tests with verbose output:

```bash
pytest -v
```

## Test Dependencies

Make sure to install the test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov
```

## Continuous Integration

These tests are executed in the CI/CD pipeline to ensure code quality. The pipeline is configured to run tests automatically on pull requests and merges to the main branch. 