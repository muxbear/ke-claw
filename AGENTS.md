# AGENTS.md - Development Guidelines for AI Agents

This document provides guidelines for AI agents working on this codebase.

## Project Overview

This is a LangGraph-based agent project that implements a skills-based agent architecture with dynamic tool loading. The project uses Python 3.10+ and follows specific conventions for code quality.

## Build, Lint, and Test Commands

### Running Tests

```bash
# Run all unit tests
make test
python -m pytest tests/unit_tests/

# Run all unit tests in a specific file
python -m pytest tests/unit_tests/test_configuration.py

# Run a specific test function
python -m pytest tests/unit_tests/test_configuration.py::test_placeholder

# Run integration tests
make integration_tests
python -m pytest tests/integration_tests/

# Run tests in watch mode (requires ptw)
make test_watch

# Run tests with profiling
make test_profile
```

### Linting and Formatting

```bash
# Run full linting (ruff + mypy)
make lint

# Run ruff only (fast)
python -m ruff check .
python -m ruff check src/
python -m ruff check tests/

# Run ruff format
python -m ruff format .
python -m ruff format src/

# Run mypy type checking (strict mode)
python -m mypy --strict src/

# Format code (ruff format + isort)
make format
make format_diff  # Only format changed files
```

### Spell Checking

```bash
make spell_check
make spell_fix
```

### Development Server

```bash
# Install dependencies
pip install -e . "langgraph-cli[inmem]"

# Start LangGraph development server
langgraph dev
```

## Code Style Guidelines

### General Principles

- **No comments unless explicitly requested** - The codebase follows a minimalist approach to comments
- **Type hints are required** - All functions must have type annotations
- **Strict mypy mode** - Code must pass `mypy --strict`

### Imports

- **Standard library first**, then third-party, then local
- Use absolute imports: `from agent.graph import graph` (not relative)
- Organize imports with ruff (will auto-sort)

### Naming Conventions

- **Functions/variables**: `snake_case` (e.g., `load_skill`, `current_skills`)
- **Classes**: `PascalCase` (e.g., `SkillState`, `SkillMiddleware`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private members**: Leading underscore (e.g., `_pre_register_all_tools`)

### Type Annotations

```python
# Use built-in generics where possible
def process_items(items: list[str]) -> dict[str, int]:
    ...

# Use Annotated for additional metadata
skills_loaded: Annotated[list[str], lambda current, new: ...]

# Prefer | over Optional for union types (Python 3.10+)
def get_skill(name: str) -> Skill | None:
    ...
```

### Error Handling

- Use `log.error()` with `exc_info=True` for exceptions
- Implement graceful degradation where appropriate (see `SkillMiddleware`)
- Return meaningful error messages to users

### Docstrings

- Use **Google-style** docstrings (configured in pyproject.toml)
- First line should be imperative mood (D401)
- Document all parameters and return values

```python
def example_function(param: str) -> bool:
    """Short description of what the function does.

    Longer description if needed.

    Args:
        param: Description of the parameter.

    Returns:
        Description of what is returned.
    """
```

### File Organization

```
src/agent/
├── __init__.py       # Exports public API
├── graph.py          # Main LangGraph definition
├── custom_llm.py     # LLM configurations
├── skills_loader.py  # Dynamic skills loader
└── skills/          # Anthropic Agent Skills (SKILL.md format)
└── utils/
    ├── tools.py      # Tool definitions
    └── log_util.py   # Logging utilities
```

### Testing Conventions

- Tests go in `tests/unit_tests/` and `tests/integration_tests/`
- Use pytest fixtures from `conftest.py`
- Test file naming: `test_<module_name>.py`
- Test function naming: `test_<description>() -> None:`

### Ruff Configuration

The project uses ruff with these rules:
- `E`, `F`: pycodestyle and pyflakes
- `I`: isort (import sorting)
- `D`: pydocstyle (Google convention)
- `UP`: pyupgrade
- `T201`: Allow `print()` statements

Ignored rules:
- `UP006`, `UP007`: Allow `list[...]` and `X | None` syntax
- `UP035`: Allow importing from `typing_extensions`
- `D417`: Don't require documentation for every parameter
- `E501`: Line length (let formatter handle it)

### Dependencies

- Core: langchain, langgraph, langchain-mcp-adapters
- LLM: langchain-deepseek
- Dev: mypy, ruff, pytest

### Environment Variables

- Copy `.env.example` to `.env` for local development
- Never commit secrets - use `.gitignore` to exclude `.env`
- Common variables: `DEEPSEEK_API_KEY`, `LANGSMITH_API_KEY`

## Common Patterns

### Creating Tools

```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """Description of what the tool does."""
    return result
```

### LangGraph State

```python
from typing import Annotated
from langchain.agents import AgentState

class CustomState(AgentState):
    custom_field: Annotated[list[str], lambda current, new: ...]
```

### Middleware Pattern

```python
class CustomMiddleware(AgentMiddleware):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        # Modify request, call handler, return response
        ...
```

## Skills (Anthropic Agent Skills)

The project follows the [Anthropic Agent Skills](https://agentskills.io) specification for defining agent capabilities.

### Directory Structure

```
skills/
├── skill-name/
│   └── SKILL.md          # Required: YAML frontmatter + Markdown instructions
├── another-skill/
│   ├── SKILL.md
│   ├── scripts/          # Optional: executable code
│   ├── references/       # Optional: documentation
│   └── assets/           # Optional: templates, images
```

### SKILL.md Format

Each skill must have a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: skill-name
description: What this skill does and when to use it.
---

# Skill Instructions

Your skill instructions here...
```

### Loading Skills

Skills are dynamically loaded from the `skills/` directory via `src/agent/skills_loader.py`:

```python
from agent.skills_loader import SKILLS  # List[dict] with name, description, content
```

### Adding a New Skill

1. Create a new directory under `skills/`
2. Add `SKILL.md` with proper frontmatter
3. The skill will be automatically loaded on next startup
