"""Rejected source records retain origin and stable reason codes."""
from .evidence import canonical


def write(path, rejects):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for reject in rejects:
            f.write(canonical(reject) + "\n")
