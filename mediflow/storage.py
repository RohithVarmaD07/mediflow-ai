"""Transactional canonical state; no extensions or remote data access."""
import json
import duckdb
from .config import PROJECT, safe_path
from .generate import ENTITIES


def connect(root):
    path = safe_path(root, root / "state" / "mediflow.duckdb")
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path), config={"threads": 2, "memory_limit": "512MB", "enable_external_access": False,
                                          "autoinstall_known_extensions": False, "autoload_known_extensions": False})
    try:
        from .compatibility import check_pending
        check_pending(con)
        con.execute((PROJECT / "sql" / "schema.sql").read_text())
    except Exception:
        con.close()
        raise
    return con


def state(con):
    result = {e: {} for e in ENTITIES}
    for entity, key, payload in con.execute("SELECT entity, id, payload FROM records ORDER BY entity,id").fetchall():
        result[entity][key] = json.loads(payload)
    return result
