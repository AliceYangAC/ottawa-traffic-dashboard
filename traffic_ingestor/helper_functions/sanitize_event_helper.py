def sanitize_event(event):
    return {
        k: str(v).encode("ascii", "backslashreplace").decode()
        if isinstance(v, str) else v
        for k, v in event.items()
    }
