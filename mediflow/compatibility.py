"""Conservative compatibility gate for committed, unpublished runs."""
import json
import platform
from importlib.metadata import version
from .config import PROJECT
from .evidence import file_hash


def fingerprint():
    files = sorted([*(PROJECT / "mediflow").glob("*.py"),
                    *(PROJECT / "sql").glob("*.sql"),
                    *(PROJECT / "config").glob("*.toml"),
                    *(PROJECT / "contracts").glob("*.json")])
    return {"format": 1, "python": platform.python_version(),
            "dependencies": {name: version(name) for name in ("duckdb", "pyarrow")},
            "files": {p.relative_to(PROJECT).as_posix(): file_hash(p) for p in files}}


def check_pending(con):
    if not con.execute("SELECT 1 FROM information_schema.tables WHERE table_name='runs' AND table_schema='main'").fetchone():
        return
    pending = con.execute("SELECT evidence FROM runs WHERE status='committed'").fetchall()
    if not pending:
        return
    current = fingerprint()
    for (payload,) in pending:
        if json.loads(payload).get("compatibility") != current:
            raise RuntimeError("INCOMPATIBLE_RECOVERY")
