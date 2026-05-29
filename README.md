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

| State | IPC |
|--------|-----|
| Signed in, idle app lock | Works — approval popup may appear for new clients |
| Signed out | Returns `locked` — use `fallback_on_locked=True` to load `.env` only |

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

| Error | When |
|--------|------|
| `ArgusConnectionError` | Socket missing, Argus not running |
| `ArgusLockedError` | Argus signed out (`status: locked`) |
| `ArgusDeniedError` | User denied or approval timed out |
| `ArgusError` | Invalid token, bad request, etc. |

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
