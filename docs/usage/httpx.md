# httpx

Pass the kwargs from `argus_httpx_config()` to `httpx.Client` or `httpx.AsyncClient`.

```python
import httpx
from useargus import load_env, argus_httpx_config

load_env()

client = httpx.Client(**argus_httpx_config(), timeout=60)
client.get("https://api.anthropic.com/v1/models", headers={...})
client.close()
```

Async:

```python
async with httpx.AsyncClient(**argus_httpx_config(), timeout=60) as client:
    r = await client.get("https://api.anthropic.com/v1/models", headers={...})
```

## `argus_httpx_config()`

Returns:

| Key | Value |
| --- | ----- |
| `proxy` | Argus proxy URL (`http://<token>@127.0.0.1:<port>`) |
| `verify` | Pre-built `ssl.SSLContext` trusting the Argus CA |
| `trust_env` | `False` |
