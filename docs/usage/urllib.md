# urllib / stdlib

Build an opener from the values returned by `argus_urllib_config()`.

```python
import urllib.request
from useargus import load_env, argus_urllib_config

load_env()

cfg = argus_urllib_config()
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler(cfg["proxy_handler"]),
    urllib.request.HTTPSHandler(context=cfg["ssl_context"]),
)

with opener.open("https://api.anthropic.com/v1/models") as resp:
    body = resp.read()
```

## `argus_urllib_config()`

Returns:

| Key | Value |
| --- | ----- |
| `proxy_handler` | `{"http": url, "https": url}` |
| `ssl_context` | `ssl.SSLContext` trusting the Argus CA |
