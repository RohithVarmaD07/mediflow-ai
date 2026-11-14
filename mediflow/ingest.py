"""Content-addressed ingestion with checksum verification."""
import json
import os
from .config import safe_path
from .evidence import file_hash
from .generate import ENTITIES
from .recovery import fault, retry


def ingest(root, batch, selected=None):
    batch = safe_path(root / "source", batch)
    manifest_path = safe_path(root, batch / "manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1.0.0" or set(manifest.get("files", {})) != set(ENTITIES):
        raise ValueError("MANIFEST_CONTRACT")
    result, hashes = [], {}
    for entity in ENTITIES:
        source = safe_path(root, batch / f"{entity}.jsonl")
        if source.stat().st_size > 20_000_000:
            raise ValueError("SOURCE_SIZE")
        sha = file_hash(source)
        if sha != manifest["files"][entity]["sha256"]:
            raise ValueError("SOURCE_HASH")
        hashes[entity] = sha
        target = safe_path(root, root / "raw" / sha / f"{entity}.jsonl")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            partial = target.with_suffix(".partial")
            with source.open("rb") as src, partial.open("wb") as dst:
                while block := src.read(65536):
                    dst.write(block)
                    fault(selected, "raw_copy")
                dst.flush()
                os.fsync(dst.fileno())
            if file_hash(partial) != sha:
                raise ValueError("COPY_HASH")
            retry(lambda: os.replace(partial, target))
        if file_hash(target) != sha:
            raise ValueError("RAW_TAMPERED")
        count = 0
        with target.open(encoding="utf-8") as f:
            for count, line in enumerate(f, 1):
                if len(line) > 16384:
                    result.append((entity, count, sha, None, "LINE_LIMIT"))
                    continue
                try:
                    row = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                    result.append((entity, count, sha, row, None))
                except (ValueError, json.JSONDecodeError):
                    result.append((entity, count, sha, None, "JSON"))
        if count != manifest["files"][entity]["rows"]:
            raise ValueError("MANIFEST_COUNT")
    return result, hashes
