# LangChain (langchain-anthropic)

Use `argus_langchain_anthropic_config()` plus `wire_langchain_anthropic_http_client()` so LangChain's internal Anthropic client uses Argus transport.

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from useargus import (
    argus_langchain_anthropic_config,
    load_env,
    wire_langchain_anthropic_http_client,
)

load_env()

cfg = argus_langchain_anthropic_config(timeout=60)
http_client = cfg["http_client"]
try:
    wire_langchain_anthropic_http_client(http_client)
    llm = ChatAnthropic(model="claude-sonnet-4-5", max_tokens=64)
    response = llm.invoke([HumanMessage(content="Reply with exactly the word: ok")])
finally:
    http_client.close()
```

See [anthropic.md](./anthropic.md) for the underlying `http_client` wiring.
