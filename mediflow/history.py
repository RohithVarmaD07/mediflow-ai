"""Bounded, additive controller records and read-only history; no database access."""
import json
import math
import re
import uuid
from itertools import islice
from pathlib import Path
from .config import APPROVED, safe_path
from .evidence import atomic_json, canonical

STAGES = ("startup", "lock", "connect", "recover", "ingest", "prepare", "commit", "publish", "finalize")
MAX_RECORDS = 64
MAX_BYTES = 8192
MAX_SCAN = 10000
FIELDS = {"schema_version", "invocation_id", "run_id", "stage_id", "attempt_id", "attempt_number",
          "sequence", "occurred_at", "elapsed_seconds", "status", "error_code", "error_type",
          "recovery_of_run_id", "evidence_refs", "root_ref", "record_type"}


def valid_uuid(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError("HISTORY_UUID")


def validate_record(record):
    if not isinstance(record, dict) or set(record) != FIELDS or record["schema_version"] != "1.0.0":
        raise ValueError("HISTORY_SCHEMA")
    for key in ("invocation_id", "attempt_id"):
        valid_uuid(record[key])
    for key in ("run_id", "recovery_of_run_id"):
        if record[key] is not None:
            valid_uuid(record[key])
    for key in ("sequence", "attempt_number"):
        if type(record[key]) is not int or record[key] < 1:
            raise ValueError("HISTORY_COUNTER")
    if record["sequence"] > MAX_RECORDS or record["stage_id"] not in STAGES:
        raise ValueError("HISTORY_LIMIT")
    if record["status"] not in {"running", "succeeded", "failed", "blocked"} or record["record_type"] != "stage_transition":
        raise ValueError("HISTORY_STATUS")
    from datetime import datetime
    stamp = record["occurred_at"]
    if not isinstance(stamp, str) or not stamp.endswith("Z"):
        raise ValueError("HISTORY_TIME")
    datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    elapsed = record["elapsed_seconds"]
    if elapsed is not None and (type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0):
        raise ValueError("HISTORY_DURATION")
    for key in ("error_code", "error_type"):
        if record[key] is not None and (not isinstance(record[key], str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]{0,63}", record[key])):
            raise ValueError("HISTORY_ERROR")
    refs = record["evidence_refs"]
    if not isinstance(refs, list) or len(refs) > 10:
        raise ValueError("HISTORY_REFERENCES")
    for ref in refs + ([record["root_ref"]] if record["root_ref"] is not None else []):
        if not isinstance(ref, str) or len(ref) > 240 or ref.startswith(("/", "\\")) or "\\" in ref or ":" in ref or ".." in ref.split("/"):
            raise ValueError("HISTORY_PATH")
        safe_path(APPROVED, APPROVED / ref)
    if len((canonical(record) + "\n").encode()) > MAX_BYTES:
        raise ValueError("HISTORY_SIZE")
    return record


def write_transition(record):
    validate_record(record)
    path = safe_path(APPROVED, APPROVED / "invocations" / record["invocation_id"] / "controller" / f"{record['sequence']:04d}.json")
    if path.exists():
        raise ValueError("HISTORY_OVERWRITE")
    atomic_json(path, record)


def read_invocation(invocation_id):
    valid_uuid(invocation_id)
    directory = safe_path(APPROVED, APPROVED / "invocations" / invocation_id / "controller")
    records, errors, attempts, flows, ordinals = [], [], {}, {}, set()
    paths = sorted(islice(directory.glob("*"), MAX_RECORDS + 1))
    if len(paths) > MAX_RECORDS:
        errors.append("HISTORY_LIMIT")
    for path in paths[:MAX_RECORDS]:
        try:
            safe_path(APPROVED, path)
            if path.suffix != ".json" or path.stat().st_size > MAX_BYTES:
                raise ValueError("HISTORY_PARTIAL_OR_SIZE")
            record = validate_record(json.loads(path.read_text(encoding="utf-8")))
            if record["invocation_id"] != invocation_id or path.name != f"{len(records)+1:04d}.json" or record["sequence"] != len(records)+1:
                raise ValueError("HISTORY_SEQUENCE")
            key = record["attempt_id"]
            identity = tuple(record[k] for k in ("run_id", "stage_id", "attempt_number", "recovery_of_run_id"))
            previous = attempts.get(key)
            if previous is None:
                if record["status"] not in {"running", "blocked"}:
                    raise ValueError("HISTORY_TRANSITION")
            elif previous != (identity, "running") or record["status"] not in {"succeeded", "failed"}:
                raise ValueError("HISTORY_TRANSITION")
            flow_key = record["recovery_of_run_id"] or "main"
            stages = ("publish", "finalize") if record["recovery_of_run_id"] else STAGES
            if record["stage_id"] not in stages:
                raise ValueError("HISTORY_STAGE")
            flow = flows.setdefault(flow_key, {})
            predecessors = stages[:stages.index(record["stage_id"])]
            if previous is None:
                ordinal = (record["run_id"], record["stage_id"], record["attempt_number"])
                if ordinal in ordinals:
                    raise ValueError("HISTORY_DUPLICATE_ATTEMPT")
                if record["status"] == "running" and any(flow.get(s) != "succeeded" for s in predecessors):
                    raise ValueError("HISTORY_DEPENDENCY")
                if record["status"] == "blocked" and not any(flow.get(s) in {"failed", "blocked"} for s in predecessors):
                    raise ValueError("HISTORY_BLOCKED_WITHOUT_FAILURE")
                ordinals.add(ordinal)
            flow[record["stage_id"]] = record["status"]
            attempts[key] = (identity, record["status"])
            records.append(record)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            errors.append(type(exc).__name__ + ":invalid_record")
    incomplete = any(status == "running" for _, status in attempts.values())
    outcome_status = None
    outcome_path = safe_path(APPROVED, APPROVED / "invocations" / f"{invocation_id}.json")
    if outcome_path.exists():
        try:
            if outcome_path.stat().st_size > MAX_BYTES:
                raise ValueError("OUTCOME_SIZE")
            outcome = json.loads(outcome_path.read_text())
            if outcome["invocation_id"] != invocation_id or outcome["status"] not in {"starting", "started", "succeeded", "startup_failed", "pipeline_failed"}:
                raise ValueError("OUTCOME_SCHEMA")
            outcome_status = outcome["status"]
        except (ValueError, TypeError, KeyError, OSError):
            errors.append("invalid_invocation_outcome")
    completed = flows.get("main", {}).get("finalize") == "succeeded" and outcome_status == "succeeded"
    failed = any(status == "failed" for _, status in attempts.values())
    status = "corrupt" if errors else ("stage_history_unavailable" if not records else
             ("succeeded" if completed and not incomplete else
              ("failed" if failed and not incomplete else "completion_not_recorded")))
    return {"invocation_id": invocation_id, "records": records, "errors": errors,
            "status": status, "reported_invocation_status": outcome_status}


def list_history(root, limit=100):
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("HISTORY_RESULT_LIMIT")
    root = safe_path(APPROVED, Path(root))
    ref = root.relative_to(APPROVED).as_posix()
    items, errors, unattributed_errors, seen_runs = [], [], [], set()
    candidates = list(islice((APPROVED / "invocations").glob("*/controller"), MAX_SCAN + 1))
    truncated = len(candidates) > MAX_SCAN
    for directory in sorted(candidates[:MAX_SCAN]):
        try:
            first = safe_path(APPROVED, directory / "0001.json")
            if first.stat().st_size > MAX_BYTES:
                raise ValueError("HISTORY_SIZE")
            header = validate_record(json.loads(first.read_text(encoding="utf-8")))
            if header["invocation_id"] != directory.parent.name:
                raise ValueError("HISTORY_IDENTITY")
        except (ValueError, KeyError, TypeError, OSError):
            unattributed_errors.append({"invocation_id": directory.parent.name, "error": "unattributed_corrupt_history"})
            continue
        if header["root_ref"] != ref:
            continue
        item = read_invocation(directory.parent.name)
        seen_runs.update(r["run_id"] for r in item["records"] if r["run_id"])
        if item["errors"]:
            errors.append({"invocation_id": item["invocation_id"], "error": "corrupt_history"})
        if len(items) < limit:
            items.append(item)
        else:
            truncated = True
    # Legacy manifests remain visible without pretending they have stage history.
    legacy = list(islice((root / "runs").glob("*/manifest.json"), MAX_SCAN + 1))
    truncated |= len(legacy) > MAX_SCAN
    for path in sorted(legacy[:MAX_SCAN]):
        if path.parent.name in seen_runs:
            continue
        try:
            safe_path(APPROVED, path)
            if path.stat().st_size > 1_000_000:
                raise ValueError("MANIFEST_SIZE")
            manifest = json.loads(path.read_text())
            valid_uuid(manifest["run_id"])
            if len(items) < limit:
                items.append({"run_id": manifest["run_id"], "status": "stage_history_unavailable", "reported_run_status": manifest["status"]})
            else:
                truncated = True
        except (ValueError, KeyError, TypeError, OSError):
            errors.append("invalid_legacy_manifest")
    return {"items": items, "errors": errors, "unattributed_errors": unattributed_errors, "truncated": truncated,
            "ordering": "invocation_id_then_legacy_run_id", "limit": limit}


def next_attempt(run_id, stage_id, root_ref):
    highest = 0
    directories = list(islice((APPROVED / "invocations").glob("*/controller"), MAX_SCAN + 1))
    if len(directories) > MAX_SCAN:
        raise ValueError("HISTORY_SCAN_LIMIT")
    for directory in directories:
        first = safe_path(APPROVED, directory / "0001.json")
        if not first.exists() or first.stat().st_size > MAX_BYTES:
            continue
        try:
            header = json.loads(first.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(header, dict) or header.get("root_ref") != root_ref:
            continue
        item = read_invocation(directory.parent.name)
        matches = [r for r in item["records"] if r["run_id"] == run_id and r["stage_id"] == stage_id]
        if matches and item["errors"]:
            raise ValueError("RECOVERY_HISTORY_CORRUPT")
        for record in matches:
            highest = max(highest, record["attempt_number"])
    return highest + 1
