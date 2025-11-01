# AI Agent Development Guide

## Test Commands
- **Run all tests**: `python -m pytest tests/ -v`
- **Run single test file**: `python -m pytest tests/unit/test_entity_service_impl.py -v`
- **Run single test**: `python -m pytest tests/unit/test_entity_service_impl.py::TestEntityService::test_add_item -v`
- **Integration tests**: `python -m pytest tests/integration/test_grpc_handlers_e2e.py -v`
- **Coverage**: `python -m pytest --cov --cov-report=html`

## Code Quality (MUST run before committing)
- **Format**: `python -m black . && python -m isort .`
- **Type check**: `python -m mypy .`
- **Lint**: `python -m flake8 .`
- **Security**: `python -m bandit -r .`

## Architecture
- **MCP Server**: `cyoda_mcp/` - Model Context Protocol tools for AI assistants
- **Core Framework**: `common/` - Auth, gRPC client, repository (CRUD), services, utils
- **Application**: `application/` - User business logic (DO NOT EDIT - for end users only)
- **Example**: `example_application/` - Templates and examples (use for testing)
- **Services**: `services/` - Service layer and dependency injection
- **Tests**: `tests/unit/`, `tests/integration/` - pytest with async support

## Code Style (Follow .augment-guidelines)
- **Python 3.10+**, Black (88 chars), isort with "black" profile
- **Type hints required**: Full mypy strict mode (except proto files)
- **Imports**: stdlib → third-party → local; use `from common.config.config import ENTITY_VERSION`
- **Naming**: snake_case (functions/vars), UPPER_CASE (constants), descriptive names
- **Functions**: Max 25-30 lines, single responsibility, early returns
- **No docstrings**: Code should be self-documenting (per .augment-guidelines)
- **Error handling**: Specific exceptions, meaningful messages, proper logging

## Cyoda Integration
- **Entity service**: Use `common/service/entity_service_interface.py` - never call repository directly
- **Auth**: `common/auth/` handles OAuth tokens automatically
- **Workflows**: Import BEFORE starting app using MCP tool `workflow_mgmt_import_workflows_from_file_tool_cyoda-mcp`
- **Entity names**: MUST match `ENTITY_NAME` constant exactly (case-sensitive)

## Installation
- **Dev setup**: `pip install -e ".[dev]"` (includes pytest, black, mypy, etc.)
- **Runtime only**: `pip install -e .`
