# TraceMind Python SDK

The official Python client for instrumenting autonomous AI agents with **TraceMind** live runtime observability and causal debugging.

## Installation

```bash
pip install -e ./sdk
```

## Quickstart

```python
import tracemind as tm

# Context manager usage automatically initializes, emits events, and runs diagnosis on completion
with tm.Session(name="Customer Support Agent Run", backend_url="http://localhost:8000") as session:
    session.emit("planning", content="Customer asking for refund on order ORD-78234")
    
    session.emit(
        "tool_call",
        content="search_knowledge_base(query='refund policy')",
        metadata={"tool_name": "search_knowledge_base", "relevance_score": 0.42}
    )
    
    session.emit(
        "observation",
        content="Retrieved policy 2023: 30 day return window",
        metadata={"source": "policy-2023"}
    )
    
    session.emit("reasoning", content="Purchase was 45 days ago. Deny refund.")
    session.emit("final_answer", content="Deny refund request.")
```

## Async Usage

```python
import asyncio
import tracemind as tm

async def main():
    async with tm.AsyncSession(name="Async Research Agent") as session:
        await session.emit("planning", content="Starting market research...")
        await session.emit("tool_call", content="web_search('Q3 cloud pricing')")
        await session.emit("final_answer", content="Research summary complete.")

asyncio.run(main())
```
