# Migration Guide: New Project Structure

This guide helps you understand the changes made to implement the new API-focused project structure.

## What Changed

### File Relocations

| Old Location | New Location | Purpose |
|--------------|--------------|----------|
| `api.py` | `src/api/v1/api.py` | Main OCR API |
| `case_management_api.py` | `src/api/v1/case_management_api.py` | Case Management API |
| `ocr_client.py` | `tools/client/ocr_client.py` | Client tools |
| `*test*.py` | `tests/` | Test files |
| `API_DOCUMENTATION.md` | `docs/api/API_DOCUMENTATION.md` | API docs |
| `CLIENT_README.md` | `docs/guides/CLIENT_README.md` | User guides |
| `requirements*.txt` | `config/` | Configuration |
| `api_examples.json` | `docs/examples/` | Examples |
| `create_sample_pdfs.py` | `tools/scripts/` | Utility scripts |
| `api_status_check.py` | `tools/monitoring/` | Monitoring tools |

### New Structure Benefits

1. **Modular Architecture**: Clear separation between API, business logic, models, and utilities
2. **Scalability**: Easy to add new API versions, services, and components
3. **Testing**: Organized test structure with unit, integration, and E2E tests
4. **Deployment**: Ready-to-use Docker and Kubernetes configurations
5. **Development**: Modern tooling with Makefile, pyproject.toml, and development workflows

## Running the Application

### Before (Old Structure)
```bash
python api.py
python case_management_api.py
```

### After (New Structure)
```bash
# Using Makefile (recommended)
make run-dev
make run-case-management

# Or directly with uvicorn
uvicorn src.api.v1.api:app --reload
uvicorn src.api.v1.case_management_api:app --reload --port 8001
```

## Development Workflow

### Setup
```bash
# Install dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Run linting
make lint
```

### Docker Development
```bash
# Build and run with Docker Compose
cd deployment/docker
docker-compose up -d
```

## Import Changes

If you have custom scripts that import from the old structure, update them:

```python
# Old imports
from api import some_function
from case_management_api import some_class

# New imports
from src.api.v1.api import some_function
from src.api.v1.case_management_api import some_class
```

## Configuration

- **Dependencies**: Now managed in `pyproject.toml` with optional dev dependencies
- **Environment**: Configuration files moved to `config/` directory
- **Data**: Sample files and outputs organized in `data/` directory

## Next Steps

1. **Update CI/CD**: Modify build scripts to use the new structure
2. **Environment Variables**: Update any deployment scripts with new paths
3. **Documentation**: Review and update any internal documentation
4. **Team Training**: Familiarize team with new development workflow

## Rollback (if needed)

If you need to rollback to the old structure temporarily:

```bash
# Copy files back to root (not recommended for production)
cp src/api/v1/api.py .
cp src/api/v1/case_management_api.py .
cp tools/client/ocr_client.py .
```

## Support

For questions about the new structure:
1. Check the main [README.md](README.md)
2. Review [API Documentation](docs/api/API_DOCUMENTATION.md)
3. Look at [examples](docs/examples/) for usage patterns