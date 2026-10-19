import re

DUR_RE = re.compile(r"(\d+)\s*(s|m|h|d|w)", re.I)
UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_duration(text: str | None) -> int | None:
    """'2d3h' -> seconds. Returns None if nothing valid was found."""
    if not text:
        return None
    text = text.strip().lower()
    if not re.fullmatch(r"(\d+\s*[smhdw]\s*)+", text):
        return None
    total = sum(int(n) * UNITS[u.lower()] for n, u in DUR_RE.findall(text))
    return total or None


def human(seconds: int) -> str:
    """seconds -> '2 days, 3 hours'"""
    seconds = int(seconds)
    parts = []
    for name, size in (("week", 604800), ("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)):
        n, seconds = divmod(seconds, size)
        if n:
            parts.append(f"{n} {name}{'s' if n != 1 else ''}")
    return ", ".join(parts[:2]) or "0 seconds"
