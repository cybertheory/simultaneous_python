# Setup Instructions

## Installation

```bash
# Install the SDK in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Verify Installation

```python
# Test imports
python -c "from simultaneous import SimClient, Browser; print('SDK installed successfully')"
```

## Running Tests

```bash
# Run all tests
pytest -q

# Run specific test file
pytest tests/test_spec.py -v

# Run with coverage
pytest --cov=simultaneous --cov-report=html
```

## Development

### Type Checking

```bash
mypy simultaneous
```

### Linting

```bash
ruff check simultaneous
ruff format simultaneous
```

## Example Usage

See `examples/scrape_minimal/` for a complete example.

```bash
cd examples/scrape_minimal
python main.py
```

## Project Structure

```
simultaneous/
  ├── __init__.py          # Public API exports
  ├── client/              # Client modules
  │   ├── sim_client.py    # Main client
  │   ├── runs.py          # Run management
  │   ├── logs.py          # Log streaming
  │   └── workflows.py     # Workflow chaining
  ├── agent/               # Agent specification
  │   ├── spec.py          # sim.yaml models
  │   ├── pack.py          # Agent packaging
  │   └── local.py         # Local runner
  ├── runtime/              # Runtime abstractions
  │   ├── base.py          # Base runtime protocol
  │   ├── browser.py       # Browser runtime
  │   ├── desktop.py       # Desktop runtime (placeholder)
  │   └── sandbox.py       # Sandbox runtime (placeholder)
  ├── providers/           # Provider adapters
  │   ├── base.py          # Provider protocol
  │   ├── router.py        # Adapter selection
  │   ├── browserbase.py   # Browserbase adapter (IMPLEMENTED)
  │   └── stagehand.py     # Stagehand adapter (STUB)
  └── utils/               # Utilities
      ├── ids.py           # ID generation
      ├── env.py           # Environment helpers
      ├── sse.py           # SSE parsing
      └── json.py          # JSON utilities
```





