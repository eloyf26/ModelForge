#!/bin/bash

# Run tests with coverage report
pytest --cov=modelforge --cov-report=term --cov-report=html tests/

# Print coverage report summary
echo "Coverage report generated in htmlcov/ directory" 