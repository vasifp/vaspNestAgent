# Development Guide

This guide covers development workflows, testing, and contributing to vaspNestAgent.

## Project Structure

```
vaspNestAgent/
├── .github/
│   └── workflows/          # CI/CD pipelines
│       ├── ci.yml          # Lint, test, build
│       └── deploy.yml      # Deploy to EKS
├── .kiro/
│   └── specs/              # Specification documents
├── docs/                   # Documentation
├── frontend/               # React frontend
│   ├── src/
│   │   ├── apollo/         # Apollo Client setup
│   │   ├── components/     # React components
│   │   ├── graphql/        # GraphQL queries
│   │   └── styles/         # CSS styles
│   ├── package.json
│   └── vite.config.ts
├── src/                    # Python backend
│   ├── agents/             # Strands agents
│   │   ├── logging.py      # LoggingAgent
│   │   ├── nest.py         # NestAgent
│   │   └── orchestration.py # OrchestrationAgent
│   ├── graphql/            # GraphQL schema
│   │   ├── resolvers.py
│   │   └── schema.py
│   ├── models/             # Data models
│   │   └── data.py
│   ├── server/             # HTTP servers
│   │   ├── graphql.py
│   │   └── health.py
│   ├── services/           # External service clients
│   │   ├── cloudwatch.py
│   │   ├── google_voice.py
│   │   └── nest_api.py
│   ├── config.py           # Configuration
│   └── main.py             # Entry point
├── terraform/              # Infrastructure as Code
│   ├── modules/            # Terraform modules
│   └── main.tf
├── tests/                  # Test suite
│   ├── integration/        # Integration tests
│   ├── property/           # Property-based tests
│   └── unit/               # Unit tests
├── Dockerfile              # Backend container
├── pyproject.toml          # Python project config
└── README.md
```

## Development Setup

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run linting
npm run lint

# Run type checking
npm run type-check
```

## Testing

### Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Property | `tests/property/` | Verify correctness properties with Hypothesis |
| Unit | `tests/unit/` | Test individual functions |
| Integration | `tests/integration/` | Test component interactions |

### Running Tests

```bash
# All tests
pytest tests/ -v

# Property tests only
pytest tests/property/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/property/test_temperature_logic.py -v

# Specific test
pytest tests/property/test_temperature_logic.py::TestTemperatureAdjustmentLogic::test_adjustment_needed_when_differential_below_threshold -v
```

### Hypothesis Profiles

```bash
# CI profile (no deadline, more examples)
pytest tests/property/ --hypothesis-profile=ci

# Debug profile (verbose output)
pytest tests/property/ --hypothesis-profile=debug
```

### Property-Based Testing

The project uses Hypothesis for property-based testing. Each test verifies a correctness property:

```python
from hypothesis import given, strategies as st

class TestTemperatureAdjustmentLogic:
    """Property 1: Temperature Adjustment Logic"""

    @given(
        ambient=st.floats(min_value=50, max_value=90),
        target=st.floats(min_value=50, max_value=90),
        threshold=st.floats(min_value=1, max_value=20),
    )
    def test_adjustment_needed_when_differential_below_threshold(
        self, ambient: float, target: float, threshold: float
    ):
        """Adjustment needed when (target - ambient) < threshold."""
        result = should_adjust_temperature(ambient, target, threshold)
        expected = (target - ambient) < threshold
        assert result == expected
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Watch mode
npm run test:watch
```

## Code Style

### Python

- **Formatter:** Ruff
- **Linter:** Ruff
- **Type Checker:** MyPy
- **Line Length:** 100 characters

```bash
# Format code
ruff format src/ tests/

# Fix linting issues
ruff check --fix src/ tests/
```

### TypeScript

- **Linter:** ESLint
- **Type Checker:** TypeScript

```bash
cd frontend
npm run lint -- --fix
```

## Adding New Features

### 1. Update Specification

Edit `.kiro/specs/nest-thermostat-agent/requirements.md` to add new requirements.

### 2. Update Design

Edit `.kiro/specs/nest-thermostat-agent/design.md` to add:
- New correctness properties
- Architecture changes
- API changes

### 3. Write Tests First

Add property tests in `tests/property/`:

```python
# tests/property/test_new_feature.py
class TestNewFeature:
    """Property X: New Feature Description"""

    @given(...)
    def test_new_property(self, ...):
        """Test description."""
        # Test implementation
```

### 4. Implement Feature

Add implementation in `src/`:

```python
# src/agents/orchestration.py
def new_feature_function(...):
    """Implement new feature.
    
    Property X: New Feature Description
    
    Args:
        ...
        
    Returns:
        ...
    """
    # Implementation
```

### 5. Update Documentation

- Add docstrings to all new functions/classes
- Update relevant docs in `docs/`
- Update README if needed

### 6. Run Tests

```bash
pytest tests/ -v
```

## Debugging

### Local Debugging

```python
# Add to code
import structlog
logger = structlog.get_logger(__name__)

logger.debug("Debug message", variable=value)
logger.info("Info message")
logger.error("Error message", error=str(e))
```

### VS Code Launch Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: vaspNestAgent",
      "type": "python",
      "request": "launch",
      "module": "src.main",
      "args": ["--local"],
      "envFile": "${workspaceFolder}/.env"
    },
    {
      "name": "Python: Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v", "-s"]
    }
  ]
}
```

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:

```
feat: Add new temperature alert feature
fix: Correct cooldown period calculation
docs: Update API reference
test: Add property tests for rate limiting
refactor: Extract notification logic to service
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes and add tests
3. Run full test suite
4. Create PR with description
5. Wait for CI to pass
6. Request review
7. Merge after approval

## Release Process

### Version Bumping

```bash
# Update version in pyproject.toml
# Update version in frontend/package.json

# Create tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] Tag created
- [ ] GitHub release created
- [ ] Docker images pushed
- [ ] Deployed to production

## Troubleshooting Development Issues

### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e ".[dev]"
```

### Test Database Issues

```bash
# Clear Hypothesis cache
rm -rf .hypothesis/
```

### Frontend Build Issues

```bash
cd frontend
rm -rf node_modules
npm install
```

### Type Checking Errors

```bash
# Regenerate stubs
mypy --install-types
```
