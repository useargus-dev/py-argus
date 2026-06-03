# Anthropic SDK

Use `argus_anthropic_config()` to build kwargs for `Anthropic` / `AsyncAnthropic` (`http_client=`).

```python
from anthropic import Anthropic
from useargus import argus_anthropic_config, load_env

load_env()

cfg = argus_anthropic_config(timeout=60)
http_client = cfg["http_client"]
try:
    client = Anthropic(**cfg)
    models = client.models.list()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=64,
        messages=[{"role": "user", "content": "Hello"}],
    )
finally:
    http_client.close()
```

Under the hood this uses `argus_httpx_config()` — see [httpx.md](./httpx.md) for field details.

`os.environ["ANTHROPIC_API_KEY"]` holds the `argus-proxy-*` placeholder when proxy is enabled — Argus rewrites it upstream.
