# requests

`requests` does not reliably send credentials from the proxy URL on HTTPS CONNECT. Use `argus_requests_config()` for session kwargs and `create_argus_requests_proxy_adapter()` for explicit `Proxy-Authorization`.

```python
import requests
from useargus import (
    load_env,
    argus_requests_config,
    create_argus_requests_proxy_adapter,
)

load_env()

cfg = argus_requests_config()
session = requests.Session()
session.proxies.update(cfg["proxies"])
session.verify = cfg["verify"]
session.trust_env = cfg["trust_env"]

adapter = create_argus_requests_proxy_adapter()
session.mount("https://", adapter)
session.mount("http://", adapter)

session.get("https://api.anthropic.com/v1/models", headers={...})
```

## `argus_requests_config()`

Returns:

| Key | Value |
| --- | ----- |
| `proxies` | `{"http": url, "https": url}` |
| `verify` | CA bundle path (`~/.argus/ca-bundle.pem`) |
| `trust_env` | `False` |

## `create_argus_requests_proxy_adapter()`

Returns a mounted-ready `requests.adapters.HTTPAdapter` that sends `Proxy-Authorization: Basic …` on CONNECT.

Alternative: `create_argus_requests_proxy_adapter_class()` returns the adapter **class** if you need to subclass.
