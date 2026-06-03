# useargus

Load environment variables from [Argus](https://github.com/useargus-dev) over local IPC, with `.env` fallback — similar to `python-dotenv`, but secrets come from your Argus bucket when the desktop app is running.

**v0.2** — returns Argus proxy connection details so you wire any HTTP library yourself.

## Requirements

- **Python** 3.10+
- **Argus desktop** signed in (IPC socket active)
- Project `.env` with `ARGUS_BUCKET_ID` and `ARGUS_BUCKET_TOKEN` (not the secret values themselves)

## Install

```bash
pip install useargus
```

## Usage modes

### Without Argus Proxy

When proxy is **disabled** on the bucket, `load_env()` injects **real secret values** into `os.environ`. Use any HTTP client normally:

```python
import os
import httpx
from useargus import load_env

load_env()

with httpx.Client() as client:
    client.get("https://api.example.com", headers={"Authorization": f"Bearer {os.environ['API_KEY']}"})
```

### With Argus Proxy enabled

When proxy is **enabled**, proxy mappings receive **`argus-proxy-*` placeholders** — not real keys. Call `load_env()`, then wire your HTTP client with SDK helpers:

```python
import httpx
from useargus import load_env, argus_httpx_config

load_env()
client = httpx.Client(**argus_httpx_config(), timeout=60)
```

See [docs/usage](./docs/usage/README.md) for per-library guides (requests, httpx, aiohttp, Anthropic SDK, LangChain, …).

## Usage

Call `load_env()` **before** other modules read `os.environ`:

```python
from useargus import load_env

load_env()
```

When the bucket has **Argus Proxy** enabled, wire **your HTTP client** after `load_env()` using the proxy helpers (see [docs/usage](./docs/usage/README.md)).

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

### Proxy wiring

After `load_env()`, use per-library **config** helpers and **builders** where needed:

```python
from useargus import argus_httpx_config, create_argus_requests_proxy_adapter

client = httpx.Client(**argus_httpx_config(), timeout=60)
```

| Kind     | Functions                                                                                            |
| -------- | ---------------------------------------------------------------------------------------------------- |
| Config   | `argus_requests_config()`, `argus_httpx_config()`, `argus_aiohttp_config()`, `argus_urllib_config()` |
| Builders | `create_argus_requests_proxy_adapter()` / `create_argus_requests_proxy_adapter_class()`              |

Per-library copy-paste examples: **[docs/usage/](./docs/usage/README.md)**

Low-level IPC fields remain on `require_proxy_config()` / `get_proxy_config()`.

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

| Error                       | Argus IPC                     | When                                            |
| --------------------------- | ----------------------------- | ----------------------------------------------- |
| `ArgusConnectionError`      | —                             | Socket/pipe missing, timeout, connection closed |
| `ArgusLockedError`          | `status: locked`              | Argus signed out                                |
| `ArgusApprovalDeniedError`  | `denied` + `APPROVAL_DENIED`  | User rejected client access                     |
| `ArgusApprovalTimeoutError` | `denied` + `APPROVAL_TIMEOUT` | Approval dialog timed out (120s)                |
| `ArgusBucketNotFoundError`  | `BUCKET_NOT_FOUND`            | Wrong `ARGUS_BUCKET_ID`                         |
| `ArgusInvalidTokenError`    | `INVALID_TOKEN`               | Wrong or rotated `ARGUS_BUCKET_TOKEN`           |
| `ArgusBucketInactiveError`  | `BUCKET_INACTIVE`             | Bucket paused in Argus                          |
| `ArgusPeerResolveError`     | `PEER_RESOLVE`                | Argus could not identify this process           |
| `ArgusProxyError`           | `PROXY_ERROR`                 | Proxy enabled but misconfigured                 |
| `ArgusInvalidRequestError`  | `INVALID_REQUEST`             | Malformed IPC request                           |
| `ArgusInvalidResponseError` | —                             | Unexpected Argus response                       |
| `ArgusConfigureError`       | —                             | Proxy unavailable or disabled for bucket        |
| `ArgusError`                | other `error` codes           | `DB_ERROR`, `INTERNAL_ERROR`, etc.              |

## Proxy cookbook

Call `load_env()` first in every example. Full guides: **[docs/usage/](./docs/usage/README.md)**

### `requests`

```python
import requests
from useargus import load_env, argus_requests_config, create_argus_requests_proxy_adapter

load_env()
cfg = argus_requests_config()
session = requests.Session()
session.proxies.update(cfg["proxies"])
session.verify = cfg["verify"]
session.trust_env = cfg["trust_env"]
adapter = create_argus_requests_proxy_adapter()
session.mount("https://", adapter)
session.mount("http://", adapter)
```

### `httpx`

```python
import httpx
from useargus import load_env, argus_httpx_config

load_env()
client = httpx.Client(**argus_httpx_config(), timeout=30)
```

### Other libraries

See [docs/usage/](./docs/usage/README.md) for aiohttp, urllib, Anthropic SDK, and LangChain.

## Package layout

- `useargus/env/load.py` — `load_env`
- `useargus/proxy/config.py` — `get_proxy_config`, `require_proxy_config`, `proxy_url`
- `useargus/proxy/wiring.py` — per-library proxy config and builders
- `useargus/ipc/client.py` — IPC client, `ProxyConfig`
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
3. Enter the version (e.g. `0.2.0` or `v0.2.0`).

The workflow runs CI, sets `pyproject.toml` version, publishes to PyPI, tags `v<version>`, and creates a GitHub release.

## License

MIT
