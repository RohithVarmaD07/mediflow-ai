"""Durable, bounded run evidence."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import time


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as f:
        f.write(canonical(value) + "\n")
        f.flush()
        os.fsync(f.fileno())
    from .recovery import retry
    retry(lambda: os.replace(temporary, path))


def event(directory, state, **details):
    with (Path(directory) / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(canonical({"occurred_at": now(), "state": state, **details}) + "\n")
        f.flush()
        os.fsync(f.fileno())


def clock():
    return time.perf_counter()
