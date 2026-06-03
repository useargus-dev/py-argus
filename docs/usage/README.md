# Proxy wiring (Python)

When **Argus Proxy** is enabled on your bucket, call `load_env()` first. Env vars for proxy-enabled mappings hold `argus-proxy-*` placeholders — not real API keys. Wire your HTTP client using the helpers below.

## Helpers

| Kind | What | Functions |
| ---- | ---- | --------- |
| **Config** | Kwargs / values for a specific library | `argus_requests_config()`, `argus_httpx_config()`, `argus_aiohttp_config()`, `argus_urllib_config()` |
| **Builders** | Non-serializable wiring (e.g. requests adapter) | `create_argus_requests_proxy_adapter()` |

Low-level IPC fields (`http_proxy`, `ca_bundle_path`, …) remain on `require_proxy_config()` / `get_proxy_config()`.

## Per-library guides

| Library | Guide |
| ------- | ----- |
| [requests](./requests.md) | config + adapter (CONNECT auth) |
| [httpx](./httpx.md) | config kwargs |
| [aiohttp](./aiohttp.md) | config values |
| [urllib / stdlib](./urllib.md) | config values |
| [Anthropic SDK](./anthropic.md) | via httpx |
| [LangChain](./langchain.md) | via httpx |

## Prerequisites

Every example assumes:

```python
from useargus import load_env

load_env()
```

Install the HTTP library in **your app** — `useargus` does not bundle `requests`, `httpx`, etc.
