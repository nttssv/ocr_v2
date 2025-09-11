# Migration Guide: Test Organization and Structure Updates

This guide helps you understand the changes made to organize the test suite and improve project structure.

## What Changed

### Test Organization

| Old Location | New Location | Purpose |
|--------------|--------------|----------|
| `final_test.py` | `tests/integration/final_test.py` | Integration tests |
| `integration_test.py` | `tests/integration/integration_test.py` | API integration tests |
| `test_*.py` (various) | `tests/e2e/` | End-to-end tests |
| `test_config.py` | `tests/unit/test_config.py` | Test configuration |

### Current Project Structure

| Component | Location | Purpose |
|-----------|----------|----------|
| `api.py` | Root directory | Main OCR API |
| `case_management_api.py` | Root directory | Case Management API |
| `ocr_client.py` | Root directory | Client tools |
| Test files | `tests/unit/`, `tests/integration/`, `tests/e2e/` | Organized test suite |
| Documentation | `docs/` | Project documentation |
| Sample files | `samples/` | Test data |

### Test Organization Benefits

1. **Clear Test Categories**: Separated unit, integration, and end-to-end tests
2. **Better Test Discovery**: Tests are organized by type and purpose
3. **Improved Maintainability**: Easier to run specific test suites
4. **Consistent Structure**: Follows pytest best practices
5. **Isolated Test Environments**: Each test type has its own configuration

## Running the Application

### Current Structure
```bash
# Start the main OCR API
python api.py

# Start the case management API (separate terminal)
python case_management_api.py

# Using Makefile (if available)
make run-dev
make run-case-management
```

## Testing Workflow

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run with verbose output
pytest tests/ -v

# Using Makefile (if available)
make test
make test-unit
make test-integration
make test-e2e
```

### Test Development
```bash
# Add new unit tests
# Place in tests/unit/

# Add new integration tests
# Place in tests/integration/

# Add new e2e tests
# Place in tests/e2e/
```

## Test Import Changes

If you have test files that need to import test utilities:

```python
# Import test configuration
from tests.unit.test_config import TestEnvironment

# Import test fixtures
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from unit.test_config import TestEnvironment
```

## Test Configuration

- **Test Structure**: Tests organized in `tests/unit/`, `tests/integration/`, `tests/e2e/`
- **Test Data**: Sample files in `samples/` directory
- **Test Outputs**: Results stored in `output/` directory
- **Test Configuration**: Shared test utilities in `tests/unit/test_config.py`

## Next Steps

1. **Test Coverage**: Add more unit tests for core functionality
2. **Test Automation**: Set up CI/CD pipeline for automated testing
3. **Test Documentation**: Document test scenarios and expected outcomes
4. **Performance Testing**: Add performance benchmarks and load tests

## Test File Locations

Current test file organization:

```bash
tests/
├── unit/
│   └── test_config.py          # Test configuration and utilities
├── integration/
│   ├── final_test.py           # Comprehensive integration tests
│   └── integration_test.py     # API integration tests
└── e2e/
    ├── realtime_api_test.py    # Real-time API testing
    ├── test_all_samples.py     # Sample processing tests
    ├── test_hierarchy_enhancement.py  # Hierarchy feature tests
    └── test_samples_hierarchy.py      # Sample hierarchy tests
```

## Support

For questions about the test structure:
1. Check the main [README.md](README.md)
2. Review test files in `tests/` directory
3. Run `pytest --help` for testing options
4. Check [docs/README.md](docs/README.md) for comprehensive testing guide