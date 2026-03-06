# Contributing to netmap

Thank you for your interest in contributing to netmap! This guide covers everything you need to get started.

## Setup

### Prerequisites

- Python 3.11 or later
- PostgreSQL 16 (or use Docker Compose)
- Git

### Development Environment

1. Clone the repository and create a branch:

```bash
git clone https://github.com/Thebul500/netmap.git
cd netmap
git checkout -b your-feature-branch
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

3. Start the database with Docker Compose:

```bash
docker compose up -d postgres
```

4. Run the development server:

```bash
uvicorn netmap.app:app --reload
```

The API will be available at `http://localhost:8000`. Verify with `curl http://localhost:8000/health`.

## Tests

### Running the Test Suite

The project uses pytest with async support. A PostgreSQL database is required for integration tests.

```bash
# Run all tests with coverage
pytest --cov=src/netmap -v

# Run a specific test file
pytest tests/test_app.py -v

# Run a specific test by name
pytest -k "test_health" -v
```

For local testing, set the database URL:

```bash
export NETMAP_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/netmap
```

### Linting and Type Checking

All code must pass linting, type checking, and security scanning before merge:

```bash
# Lint with ruff
ruff check src/

# Type check with mypy
mypy src/netmap/ --ignore-missing-imports

# Security scan with bandit
bandit -r src/netmap/ -q
```

These checks run automatically in CI on every push and pull request.

## Pull Requests

### Before You Start

- Check the existing issues to avoid duplicate work.
- For large changes, open an issue first to discuss your approach.

### PR Process

1. **Create a feature branch** from `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-change
```

2. **Make your changes** following the project conventions:
   - Use async/await for all I/O operations.
   - Add Pydantic schemas for request/response models.
   - Use proper HTTP status codes and error responses.
   - Keep line length under 100 characters (configured in ruff).

3. **Write tests** for any new functionality. Place tests in the `tests/` directory following the existing naming pattern (`test_<module>.py`).

4. **Run the full check suite** before pushing:

```bash
pytest --cov=src/netmap -v
ruff check src/
mypy src/netmap/ --ignore-missing-imports
bandit -r src/netmap/ -q
```

5. **Push and open a PR** against `main`:

```bash
git push origin feature/your-change
```

6. **In your PR description**, include:
   - A clear summary of what changed and why.
   - Any related issue numbers (e.g., "Closes #42").
   - Steps to test the change manually, if applicable.

7. **CI must pass** before the PR can be merged. The CI pipeline runs tests, linting, type checking, and security scanning automatically.

### Code Style

- Follow existing patterns in the codebase.
- Use type annotations on function signatures.
- Async SQLAlchemy sessions for all database operations.
- FastAPI dependency injection for shared resources (database sessions, auth).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
