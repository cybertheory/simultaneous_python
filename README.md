# Simultaneous SDK

Python SDK for Simultaneous - run agents across multiple providers with a unified API.

## Features

- **Provider-agnostic API**: Run agents on Browserbase and more providers
- **Browser automation SDK**: Use Stagehand (or Playwright) inside your agent code
- **Flexible runtime configuration**: Browser, Desktop, and Sandbox runtimes
- **Agent packaging**: Define agents with `sim.yaml` and package automatically
- **Parallel execution**: Run agents across multiple shards
- **Workflow chaining**: Chain multiple agents together
- **Backwards compatible**: Use existing Stagehand/Playwright scripts

## Installation

### Quick Install

```bash
# Install from source with all dependencies
pip install -e ".[dev]"
```

### Basic Install

```bash
# Install from source (production dependencies only)
pip install -e .
```

### Verify Installation

```bash
# Test imports
python -c "from simultaneous import SimClient, Browser, BrowserClient; print('✅ SDK installed')"

# Or run the quick test script
python simultaneous/QUICK_TEST.py
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Quick Start

### Simple Mode (Provider-agnostic)

```python
from simultaneous import SimClient, Browser, BrowserClient

client = SimClient(api_key="SIM_...")  # Optional for MVP

@client.agent(name="scrape-jobs", runtime=Browser(provider="browserbase"))
async def scrape_jobs(query: str) -> list[dict]:
    """Scrape job listings using BrowserClient."""
    # Use BrowserClient inside your agent code for browser automation
    browser = BrowserClient(session_url="wss://...")
    page = await browser.new_page()
    await page.goto(f"https://example.com/search?q={query}")
    # ... automation code
    return []

# Run with parallel shards
run_id = await client.run(
    "scrape-jobs",
    params={"query": "sap payroll"},
    parallel=50
)

# Stream logs
await client.logs.stream(run_id)

# Wait for completion
result = await client.runs.wait(run_id)
print(f"Status: {result['state']}")
```

### Advanced Mode (Explicit Provider)

```python
from simultaneous import Browser

bb = Browser(
    provider="browserbase",
    region="sfo",
    project="proj_123"
)

run_id = await client.run(
    "scrape-jobs",
    params={"query": "sap"},
    runtime=bb,
    parallel=10
)
```

### Minimal Workflow (Linear Chaining)

```python
pipe = client.workflow.chain("scrape-jobs", "normalize")
run_id = await client.workflow.run(
    pipe,
    params={"query": "sap"}
)
```

## Agent Specification (sim.yaml)

Create a `sim.yaml` file to define your agent:

```yaml
name: scrape-jobs
version: 1.0.0
description: Scrape job listings
runtime:
  type: browser           # browser | desktop | sandbox
  provider: auto          # auto | browserbase | self
  region: auto
entrypoint:
  command: ["python", "main.py"]
inputs:
  - name: query
    type: string
    description: Search query
outputs:
  - name: rows
    type: json
secrets: []
permissions:
  network: ["*"]
timeouts:
  hard_seconds: 900
```

## Environment Variables

### Simultaneous API

- `SIMULTANEOUS_API_KEY`: Your Simultaneous API key (optional for MVP)
- `SIMULTANEOUS_API_URL`: Simultaneous API base URL (defaults to `https://api.simultaneous.live`)
- `SIMULTANEOUS_PROJECT_ID`: Simultaneous project ID (UUID) - required when using providers

### Browserbase (via Simultaneous API)

- `BROWSERBASE_REGION`: Browserbase region (default: "sfo")

**Note**: The SDK now uses the Simultaneous API (`https://api.simultaneous.live`) to create Browserbase sessions. The provider adapter calls the Simultaneous API, which then creates a Browserbase session and returns a session URL. This session URL is then used with the BrowserClient browser automation client.

## Example Agent

See `examples/scrape_minimal/` for a complete example:

```bash
cd examples/scrape_minimal
# Run with SDK
python -m simultaneous.run main.py --query "test"
```

## Development

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run quick test
python simultaneous/QUICK_TEST.py

# Run all tests
pytest -q

# Run specific test file
pytest tests/test_router.py -v

# Type checking
mypy simultaneous

# Linting
ruff check simultaneous
```

See [TESTING.md](TESTING.md) for detailed testing instructions.

### Project Structure

```
simultaneous/
  __init__.py
  client/          # Client APIs
    sim_client.py  # Main client
    browser.py     # Browser automation clients (BrowserClient)
    runs.py        # Run management
    logs.py        # Log streaming
    workflows.py   # Workflow chaining
  agent/           # Agent specification
    spec.py        # sim.yaml models
    pack.py        # Agent packaging
    local.py       # Local runner
  runtime/         # Runtime abstractions
    base.py        # Base runtime protocol
    browser.py     # Browser runtime
    desktop.py     # Desktop runtime (placeholder)
    sandbox.py     # Sandbox runtime (placeholder)
  providers/       # Provider adapters (infrastructure)
    base.py        # Provider protocol
    router.py      # Adapter selection
    browserbase.py # Browserbase adapter (infrastructure provider)
  utils/           # Utilities
    ids.py         # ID generation
    env.py         # Environment helpers
    sse.py         # SSE parsing
    json.py        # JSON utilities
```

## Using BrowserClient in Your Agents

BrowserClient is a browser automation client wrapper that you can use inside your agent code.
The provider (e.g., Browserbase) provides the infrastructure where your agent runs.

### Using BrowserClient in Agent Code

```python
from simultaneous import SimClient, Browser, BrowserClient

client = SimClient(api_key="SIM_...")

@client.agent(name="scrape", runtime=Browser(provider="browserbase"))
async def scrape(query: str):
    # The provider (Browserbase) creates a session via Simultaneous API
    # and returns a session URL. BrowserClient connects to this URL.
    browser = BrowserClient(session_url="wss://...")  # URL from provider
    page = await browser.new_page()
    await page.goto(f"https://example.com/search?q={query}")
    # ... your automation code
    return results
```

### Architecture

**Flow:**
1. **SDK Client** → Calls Simultaneous API (`https://api.simultaneous.live`)
2. **Simultaneous API** → Creates Browserbase session via Browserbase adapter
3. **Provider Adapter** → Returns session URL (WebSocket endpoint)
4. **Browser Client (BrowserClient)** → Connects to session URL and exposes browser automation primitives

**Components:**
- **Provider (Browserbase via Simultaneous API)**: Creates browser sessions and returns session URLs
- **Browser Client (BrowserClient)**: Connects to session URL and provides browser automation primitives

### Using Existing Playwright Scripts

```python
# Package existing Playwright script
from simultaneous.agent import pack_agent

bundle_path = pack_agent("./my-playwright-script")
# Now run with Simultaneous SDK
```

## Roadmap

- [ ] Complete BrowserClient browser automation integration
- [ ] Desktop and Sandbox runtime support
- [ ] Additional infrastructure providers (beyond Browserbase)
- [ ] Remote control-plane mode
- [ ] Secrets broker integration
- [ ] Multi-provider single-agent execution
- [ ] Shared auth profiles and context
- [ ] TypeScript/Node SDK parity

## License

MIT
