# OCR API with Case Management

A modern, scalable OCR API system with advanced case management capabilities, built following API best practices.

## Quick Start

```bash
# Install dependencies
make install-dev

# Run development server
make run-dev

# Run case management API
make run-case-management

# Run tests
make test
```

## Project Structure

This project follows modern API development best practices with a modular, scalable architecture:

```
ocr_test/
├── src/                          # Source code
│   ├── api/                      # API layer
│   │   └── v1/                   # API version 1
│   │       ├── endpoints/        # API endpoints
│   │       ├── middleware/       # Custom middleware
│   │       ├── schemas/          # Pydantic schemas
│   │       ├── api.py           # Main API application
│   │       └── case_management_api.py  # Case management API
│   ├── core/                     # Business logic
│   │   ├── services/            # Business services
│   │   ├── processors/          # OCR processors
│   │   └── exceptions/          # Custom exceptions
│   ├── models/                   # Data models
│   │   ├── database/            # Database models
│   │   ├── schemas/             # Data schemas
│   │   └── entities/            # Domain entities
│   ├── utils/                    # Utilities
│   │   ├── helpers/             # Helper functions
│   │   └── validators/          # Data validators
│   └── workers/                  # Background workers
│       ├── ocr/                 # OCR workers
│       └── background/          # Background tasks
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── e2e/                     # End-to-end tests
│   └── fixtures/                # Test fixtures
├── deployment/                   # Deployment configurations
│   ├── docker/                  # Docker configurations
│   ├── kubernetes/              # Kubernetes manifests
│   └── scripts/                 # Deployment scripts
├── docs/                         # Documentation
│   ├── api/                     # API documentation
│   ├── guides/                  # User guides
│   └── examples/                # Code examples
├── tools/                        # Development tools
│   ├── client/                  # Client tools
│   ├── scripts/                 # Utility scripts
│   └── monitoring/              # Monitoring tools
├── data/                         # Data storage
│   ├── samples/                 # Sample files
│   ├── uploads/                 # Upload directory
│   └── outputs/                 # Output directory
├── config/                       # Configuration files
│   ├── environments/            # Environment configs
│   └── logging/                 # Logging configs
├── pyproject.toml               # Project configuration
├── Makefile                     # Development commands
└── README.md                    # This file
```

## Features

- **Simple OCR API**: Direct PDF to text conversion
- **Case Management System**: Advanced workflow management for complex document processing
- **Modular Architecture**: Clean separation of concerns
- **Containerized Deployment**: Docker and Kubernetes support
- **Comprehensive Testing**: Unit, integration, and E2E tests
- **Development Tools**: Linting, formatting, and monitoring
- **Production Ready**: Scalable and maintainable codebase

## Development Workflow

### 1. Setup Development Environment
```bash
# Create virtual environment
make setup-env
source venv/bin/activate

# Install dependencies
make install-dev
```

### 2. Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Run tests with coverage
make test-coverage
```

### 3. Running Services
```bash
# Development mode
make run-dev              # OCR API on port 8000
make run-case-management  # Case Management API on port 8001

# Production mode
make run-prod
```

### 4. Docker Deployment
```bash
# Build and run with Docker
make docker-build
make docker-run

# Or use docker-compose
cd deployment/docker
docker-compose up -d
```

## API Documentation

- **API Documentation**: [docs/api/API_DOCUMENTATION.md](docs/api/API_DOCUMENTATION.md)
- **Client Guide**: [docs/guides/CLIENT_README.md](docs/guides/CLIENT_README.md)
- **Examples**: [docs/examples/](docs/examples/)

## Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Generate coverage report
make test-coverage
```

## Deployment

### Docker
```bash
# Local development
docker-compose -f deployment/docker/docker-compose.yml up -d
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f deployment/kubernetes/
```

## Contributing

1. Follow the established project structure
2. Write tests for new features
3. Run `make format` and `make lint` before committing
4. Update documentation as needed

## License

MIT License - see LICENSE file for details.