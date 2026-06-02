# useargus

Load environment variables from [Argus](https://github.com/useargus-dev) over local IPC, with `.env` fallback — similar to `python-dotenv`, but secrets come from your Argus bucket when the desktop app is running.

## Requirements

- **Python** 3.10+
- **Argus desktop** signed in (IPC socket active)
- Project `.env` with `ARGUS_BUCKET_ID` and `ARGUS_BUCKET_TOKEN` (not the secret values themselves)

## Install

```bash
pip install useargus
```

## Usage

Call `load_env()` **before** other modules read `os.environ`:

```python
from useargus import load_env

load_env()
```

When the bucket has **Argus Proxy** enabled, wire **your HTTP client explicitly** after `load_env()` (see [Proxy cookbook](#proxy-cookbook)). Proxy-enabled mappings receive `argus-proxy-*` placeholders instead of real API keys.

### Migration from python-dotenv

```python
# Before
from dotenv import load_dotenv
load_dotenv()

# After
from useargus import load_env
load_env()
```

## Project `.env`

```env
ARGUS_BUCKET_ID=550e8400-e29b-41d4-a716-446655440000
ARGUS_BUCKET_TOKEN=tok_...

# Optional local overrides (override bucket values for the same key)
# DATABASE_URL=postgresql://localhost/dev
```

Copy `.env.example` to get started.

## How it works

1. Parse `.env` (no side effects yet).
2. If `ARGUS_BUCKET_ID` and `ARGUS_BUCKET_TOKEN` are set (OS env or `.env`), connect to Argus over IPC and fetch mapped secrets.
3. Apply bucket values to `os.environ`.
4. Apply `.env` — **duplicate keys use the `.env` value** (overrides bucket).
5. If bucket credentials are missing, load `.env` only (standard dotenv behavior).

### Argus app lock vs sign-out

| State                    | IPC                                                                  |
| ------------------------ | -------------------------------------------------------------------- |
| Signed in, idle app lock | Works — approval popup may appear for new clients                    |
| Signed out               | Returns `locked` — use `fallback_on_locked=True` to load `.env` only |

Idle **app lock** does **not** block IPC. Only **sign-out** returns IPC `locked`.

### First run

The first time a process connects, Argus shows an **access approval** dialog (up to ~120s). Later requests use the grant TTL from bucket settings.

## API

### `load_env(...)`

```python
from useargus import load_env

result = load_env(
    path=".env",                 # default: .env in cwd
    override=False,              # dotenv-only mode: don't override existing OS env
    timeout_ms=130_000,          # IPC timeout
    fallback_on_locked=False,    # if signed out, load .env instead of raising
)

# result.source == "bucket" | "dotenv"
# result.keys — names set (never values)
```

### Proxy factories (preferred)

After `load_env()`, use one factory per HTTP library — **no global monkey patches**:

| Factory | Use with |
|---------|----------|
| `create_proxy_agents()` | Low-level proxy URL + CA + auth header |
| `requests_session()` | `requests` |
| `httpx_client()` / `httpx_async_client()` | `httpx` |
| `anthropic_http_client()` | `anthropic` SDK, LangChain |
| `aiohttp_session()` | `aiohttp` |
| `ssl_context()` | `urllib` / `http.client` |

### `configure(client=None)` (deprecated)

`configure()` without arguments is **deprecated** (warns; removed next major). Use factories above.

### `load_proxies(...)` (deprecated)

Use factory helpers instead.

### `fetch_bucket_env(...)`

Lower-level IPC call if you only need the bucket map:

```python
import os

from useargus import fetch_bucket_env

env = fetch_bucket_env(
    bucket_id=os.environ["ARGUS_BUCKET_ID"],
    client_token=os.environ["ARGUS_BUCKET_TOKEN"],
)
```

### Errors

All errors extend `ArgusError` with `.code` and optional `.request_id`. Catch specific types for programmatic handling:

| Error | Argus IPC | When |
| ----- | --------- | ---- |
| `ArgusConnectionError` | — | Socket/pipe missing, timeout, connection closed |
| `ArgusLockedError` | `status: locked` | Argus signed out |
| `ArgusApprovalDeniedError` | `denied` + `APPROVAL_DENIED` | User rejected client access |
| `ArgusApprovalTimeoutError` | `denied` + `APPROVAL_TIMEOUT` | Approval dialog timed out (120s) |
| `ArgusBucketNotFoundError` | `BUCKET_NOT_FOUND` | Wrong `ARGUS_BUCKET_ID` |
| `ArgusInvalidTokenError` | `INVALID_TOKEN` | Wrong or rotated `ARGUS_BUCKET_TOKEN` |
| `ArgusBucketInactiveError` | `BUCKET_INACTIVE` | Bucket paused in Argus |
| `ArgusPeerResolveError` | `PEER_RESOLVE` | Argus could not identify this process |
| `ArgusProxyError` | `PROXY_ERROR` | Proxy enabled but misconfigured |
| `ArgusInvalidRequestError` | `INVALID_REQUEST` | Malformed IPC request |
| `ArgusInvalidResponseError` | — | Unexpected Argus response |
| `ArgusConfigureError` | — | `configure()` preconditions or unsupported client |
| `ArgusError` | other `error` codes | `DB_ERROR`, `INTERNAL_ERROR`, etc. |

## Proxy cookbook

Call `load_env()` first in every example.

### `requests`

```python
from useargus import load_env, requests_session

load_env()
session = requests_session()
session.get("https://api.anthropic.com/v1/models", headers={...})
```

### `httpx`

```python
from useargus import load_env, httpx_client

load_env()
client = httpx_client(timeout=30)
client.get("https://api.anthropic.com/v1/models", headers={...})
client.close()
```

### `anthropic` SDK

```python
from anthropic import Anthropic
from useargus import load_env, anthropic_http_client

load_env()
client = Anthropic(http_client=anthropic_http_client(timeout=60))
```

### LangChain (`langchain-anthropic`)

```python
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic
from useargus import load_env, anthropic_http_client

load_env()
anthropic = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
    http_client=anthropic_http_client(timeout=60),
)
llm = ChatAnthropic(model="claude-sonnet-4-5", client=anthropic)
```

### `aiohttp`

```python
from useargus import load_env, aiohttp_session

load_env()
session = aiohttp_session()
async with session.get("https://api.anthropic.com/v1/models", headers={...}) as r:
    ...
```

### `urllib` / stdlib

```python
import urllib.request
from useargus import load_env, create_proxy_agents, ssl_context

load_env()
agents = create_proxy_agents()
ctx = ssl_context()
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"https": agents.proxy_url}),
    urllib.request.HTTPSHandler(context=ctx),
)
```

### BAML

Configure the HTTP client BAML uses (typically `httpx_client()`) and pass it to your generated client setup.

## Package layout

Internal modules (public exports unchanged):

- `useargus/env/load.py` — `load_env`
- `useargus/proxy/factories.py` — explicit proxy wiring
- `useargus/proxy/config.py` — `get_proxy_config`, `require_proxy_config`
- `useargus/ipc/client.py` — IPC client
- `useargus/errors.py` — error types

## Development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
mypy useargus
pytest
python -m build
```

## Publish

Publishing is **manual** via GitHub Actions (adding `PYPI_TOKEN` alone does not publish).

1. Add repository secret **`PYPI_TOKEN`** (PyPI API token with publish rights).
2. Go to **Actions → Publish to PyPI → Run workflow**.
3. Enter the version (e.g. `0.1.0` or `v0.1.0`).

The workflow runs CI, sets `pyproject.toml` version, publishes to PyPI, tags `v<version>`, and creates a GitHub release.

### Publish locally (optional)

```bash
pip install -e ".[dev]"
python -m build
twine upload dist/*
```

## License

MIT
