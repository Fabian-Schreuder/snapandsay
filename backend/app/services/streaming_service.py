"""Streaming service for SSE event formatting."""

from collections.abc import AsyncGenerator

from app.schemas.sse import SSEEvent


async def format_sse(event: SSEEvent) -> str:
    """
    Format an SSEEvent into SSE wire format.

    Args:
        event: The SSEEvent to format.

    Returns:
        SSE-formatted string with data prefix and double newline terminator.

    Example output:
        data: {"type": "agent.thought", "payload": {...}}

    """
    json_data = event.model_dump_json()
    return f"data: {json_data}\n\n"


async def format_sse_comment(comment: str) -> str:
    """
    Format a comment line for SSE (used for keepalive/heartbeat).

    Args:
        comment: The comment text.

    Returns:
        SSE comment format (colon-prefixed line).
    """
    return f": {comment}\n\n"


async def sse_event_generator(
    events: AsyncGenerator[SSEEvent, None],
    heartbeat_interval: float = 15.0,
) -> AsyncGenerator[str, None]:
    """
    Wrap an event generator with SSE formatting and heartbeat support.

    Args:
        events: Async generator yielding SSEEvent objects.
        heartbeat_interval: Seconds between heartbeat comments.

    Yields:
        SSE-formatted strings.
    """
    import asyncio

    last_event_time = asyncio.get_event_loop().time()

    async for event in events:
        current_time = asyncio.get_event_loop().time()

        # Send heartbeat if too much time has passed
        if current_time - last_event_time > heartbeat_interval:
            yield await format_sse_comment("heartbeat")

        yield await format_sse(event)
        last_event_time = current_time
