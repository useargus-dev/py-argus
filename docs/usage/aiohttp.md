# aiohttp

Use connector SSL from `argus_aiohttp_config()` and pass `proxy=` per request.

```python
import aiohttp
from useargus import load_env, argus_aiohttp_config

load_env()

cfg = argus_aiohttp_config()
connector = aiohttp.TCPConnector(ssl=cfg["connector_ssl"])

async with aiohttp.ClientSession(connector=connector, trust_env=cfg["trust_env"]) as session:
    async with session.get(
        "https://api.anthropic.com/v1/models",
        headers={...},
        proxy=cfg["proxy"],
    ) as resp:
        body = await resp.text()
```

## `argus_aiohttp_config()`

Returns:

| Key | Value |
| --- | ----- |
| `proxy` | Argus proxy URL |
| `trust_env` | `False` |
| `connector_ssl` | `ssl.SSLContext` trusting the Argus CA |

Pass `proxy=cfg["proxy"]` on each request (or set a default on the session if your aiohttp version supports it).
