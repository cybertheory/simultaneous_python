"""SSE (Server-Sent Events) parser."""

from typing import Iterator


def parse_sse(lines: Iterator[str]) -> Iterator[dict[str, str]]:
    """
    Parse SSE format lines into event dictionaries.
    
    Yields events as dicts with 'event', 'data', 'id', 'retry' keys.
    """
    current_event: dict[str, str] = {}
    
    for line in lines:
        line = line.rstrip("\n\r")
        
        if not line:
            # Empty line marks end of event
            if current_event:
                yield current_event
                current_event = {}
            continue
        
        if ":" in line:
            field, value = line.split(":", 1)
            field = field.strip()
            value = value.lstrip()
            
            if field == "event":
                current_event["event"] = value
            elif field == "data":
                current_event["data"] = current_event.get("data", "") + value
            elif field == "id":
                current_event["id"] = value
            elif field == "retry":
                current_event["retry"] = value
    
    # Yield last event if any
    if current_event:
        yield current_event








