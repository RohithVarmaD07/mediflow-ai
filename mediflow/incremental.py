"""Transactional pipeline with recoverable snapshot publication."""
import copy
from contextlib import ExitStack
import json
import platform
import sys
import uuid
import pyarrow as pa
from importlib.metadata import version
from pathlib import Path
from .analytics import publish
from .config import APPROVED, PROJECT, budget, runtime, safe_path
from .deduplicate import classify
from .evidence import atomic_json, canonical, clock, digest, event, file_hash, now
from .ingest import ingest
from .quarantine import write as write_quarantine
from .recovery import fault, writer_lock
from .storage import connect, state
from .compatibility import fingerprint, check_pending
from .validation import relationship_errors, validate
from .orchestration import ACTIVE, ExecutionContext, SequentialController, root_reference


def finish(con, root, run_id, evidence, selected=None):
    controller = ACTIVE.get()
    start = clock()
    operation = lambda: publish(con, root, run_id, selected)
    outputs = controller.execute_stage("publish", operation) if controller else operation()
    evidence["publication_seconds"] = clock() - start
    operation = lambda: finalize_evidence(con, root, run_id, evidence, outputs, selected)
    return controller.execute_stage("finalize", operation) if controller else operation()


def finalize_evidence(con, root, run_id, evidence, outputs, selected=None):
    directory = root / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    evidence["status"] = "succeeded"
    evidence["finished_at"] = now()
    evidence["outputs"] = outputs
    fault(selected, "evidence")
    atomic_json(directory / "outputs.json", outputs)
    atomic_json(directory / "metrics.json", {k: v for k, v in evidence.items() if k.endswith("seconds") or k in {"counts", "changes"}})
    atomic_json(directory / "reconciliation.json", evidence["reconciliation"])
    atomic_json(directory / "quality.json", {"rejected": evidence["counts"]["invalid"], "referential_integrity": "passed", "row_accounting": "passed"})
    atomic_json(directory / "manifest.json", evidence)
    event(directory, "succeeded", recovered=evidence.get("recovered", False))
    con.execute("UPDATE runs SET status='published', evidence=? WHERE run_id=?", [canonical(evidence), run_id])
    return evidence


def recover(con, root):
    check_pending(con)
    recovered = []
    for run_id, payload in con.execute("SELECT run_id,evidence FROM runs WHERE status='committed' ORDER BY run_id").fetchall():
        evidence = json.loads(payload)
        evidence["recovered"] = True
        parent = ACTIVE.get()
        if parent:
            token = ACTIVE.set(SequentialController(parent.context, run_id, recovery=True))
            try:
                finish(con, root, run_id, evidence)
            finally:
                ACTIVE.reset(token)
        else:
            finish(con, root, run_id, evidence)
        recovered.append(run_id)
    for directory in (root / "runs").glob("*"):
        path = directory / "manifest.json"
        if path.exists():
            manifest = json.loads(path.read_text())
            if manifest["status"] == "running" and not con.execute("SELECT 1 FROM runs WHERE run_id=?", [directory.name]).fetchone():
                manifest.update(status="interrupted_before_commit", finished_at=now())
                atomic_json(path, manifest)
                event(directory, "interrupted_before_commit")
    return recovered


def run(root, batch, selected=None):
    invocation_id = str(uuid.uuid4())
    outcome = {"invocation_id": invocation_id, "status": "starting", "started_at": now(), "stage": "storage"}
    # A trusted fallback location records rejected target paths and lock failures.
    path = safe_path(APPROVED, APPROVED / "invocations" / f"{invocation_id}.json")
    atomic_json(path, outcome)
    controller = SequentialController(ExecutionContext(invocation_id, root_reference(root)))
    token = ACTIVE.set(controller)
    try:
        with controller.stage("startup"):
            root = runtime(root)
            budget(100_000_000)
        outcome["stage"] = "lock"
        atomic_json(path, outcome)
        with ExitStack() as resources:
            controller.execute_stage("lock", lambda: resources.enter_context(writer_lock(root)))
            outcome["stage"] = "database"
            atomic_json(path, outcome)
            con = controller.execute_stage("connect", lambda: connect(root))
            try:
                outcome["stage"] = "recovery"
                atomic_json(path, outcome)
                recovered = controller.execute_stage("recover", lambda: recover(con, root))
                outcome.update(status="started", stage="pipeline")
                atomic_json(path, outcome)
                result = _execute(con, root, batch, selected, recovered, invocation_id)
                outcome.update(status="succeeded", run_id=result["run_id"])
                return result
            finally:
                con.close()
    except Exception as exc:
        outcome.update(status="startup_failed" if outcome["stage"] != "pipeline" else "pipeline_failed",
                       error_type=type(exc).__name__)
        if str(exc) in {"STORAGE_BUDGET", "WRITER_BUSY", "INCOMPATIBLE_RECOVERY",
                        "PATH_OUTSIDE_ROOT", "PATH_ESCAPE", "REPARSE_POINT"}:
            outcome["error_code"] = str(exc)
        raise
    finally:
        ACTIVE.reset(token)
        original_error = sys.exception()
        outcome["finished_at"] = now()
        try:
            atomic_json(path, outcome)
        except Exception as evidence_error:
            if original_error is None:
                raise
            original_error.add_note("Invocation outcome could not be persisted: " + type(evidence_error).__name__)


def _execute(con, root, batch, selected, recovered, invocation_id):
    run_id = str(uuid.uuid4())
    controller = ACTIVE.get()
    controller.run_id = run_id
    directory = root / "runs" / run_id
    directory.mkdir(parents=True)
    evidence = {"run_id": run_id, "invocation_id": invocation_id, "compatibility": fingerprint(), "status": "running", "started_at": now(), "recovered_runs": recovered,
                "python": platform.python_version(), "dependencies": {n: version(n) for n in ("duckdb", "pyarrow")},
                "source_digest": digest({str(p.relative_to(PROJECT)): file_hash(p) for p in sorted([*(PROJECT / "mediflow").glob("*.py"), *(PROJECT / "sql").glob("*.sql"), *(PROJECT / "config").glob("*.toml")])})}
    atomic_json(directory / "manifest.json", evidence)
    for name in ("metrics", "quality", "reconciliation", "outputs"):
        atomic_json(directory / f"{name}.json", {"status": "not_completed"})
    write_quarantine(directory / "quarantine.jsonl", [])
    event(directory, "started")
    start = clock()
    try:
        stage = clock()
        entries, hashes = controller.execute_stage("ingest", lambda: ingest(root, Path(batch), selected))
        evidence["ingestion_seconds"] = clock() - stage
        winners, candidate = controller.execute_stage("prepare", lambda: prepare_batch(con, directory, entries, hashes, evidence))
        controller.execute_stage("commit", lambda: commit_candidate(con, run_id, winners, candidate, evidence, start, selected))
        fault(selected, "after_commit")
        return finish(con, root, run_id, evidence, selected)
    except Exception as exc:
        committed = con.execute("SELECT 1 FROM runs WHERE run_id=?", [run_id]).fetchone()
        evidence.update(status="publication_pending" if committed else "failed", error=type(exc).__name__ + ": " + str(exc)[:500], finished_at=now())
        evidence["elapsed_before_failure_seconds"] = clock() - start
        atomic_json(directory / "metrics.json", {"status": evidence["status"], "elapsed_seconds": evidence["elapsed_before_failure_seconds"]})
        atomic_json(directory / "manifest.json", evidence)
        event(directory, evidence["status"], error=evidence["error"])
        raise


def prepare_batch(con, directory, entries, hashes, evidence):
    valid, rejects = [], []
    for entity, line, sha, row, error in entries:
        error = error or validate(entity, row)
        if error:
            rejects.append({"entity": entity, "line": line, "source_sha256": sha, "reason": error, "record": row})
        else:
            valid.append((entity, line, sha, row))
    previous = state(con)
    winners, counts, conflicts = classify(valid, previous)
    counts["invalid"] += len(rejects)
    rejects.extend(conflicts)
    candidate = copy.deepcopy(previous)
    for (entity, key), item in winners.items():
        candidate[entity][key] = item[3]
    # Reject conflicting relationships as a group, preserving the prior valid state.
    if relationship_errors(candidate):
        for item in winners.values():
            rejects.append({"entity": item[0], "line": item[1], "source_sha256": item[2], "reason": "RELATIONSHIP_BATCH", "record": item[3]})
        counts["invalid"] += len(winners)
        counts["accepted"] -= len(winners)
        winners = {}
        candidate = previous
    if relationship_errors(candidate):
        raise RuntimeError("RELATIONSHIP_INVARIANT")
    if sum(counts.values()) != len(entries):
        raise RuntimeError("ROW_ACCOUNTING_INVARIANT")
    changes = {"inserts": 0, "updates": 0, "tombstones": 0}
    for (entity, key), item in winners.items():
        changes["tombstones" if item[3]["is_deleted"] else ("updates" if key in previous[entity] else "inserts")] += 1
    write_quarantine(directory / "quarantine.jsonl", rejects)
    reconciliation = {"input_rows": len(entries), "classified_rows": sum(counts.values()), "difference": 0,
                      "before": {e: len(v) for e, v in previous.items()}, "after": {e: len(v) for e, v in candidate.items()},
                      "canonical_digest": digest(candidate)}
    evidence.update(counts=counts, changes=changes, input_hashes=hashes, reconciliation=reconciliation)
    atomic_json(directory / "manifest.json", evidence)
    atomic_json(directory / "reconciliation.json", reconciliation)
    return winners, candidate


def commit_candidate(con, run_id, winners, candidate, evidence, start, selected=None):
    stage = clock()
    con.execute("BEGIN TRANSACTION")
    try:
        if winners:
            incoming = pa.Table.from_pylist(
                [{"entity": entity, "id": key, "version": item[3]["source_version"], "payload": canonical(item[3])}
                 for (entity, key), item in winners.items()],
                schema=pa.schema([("entity", pa.string()), ("id", pa.string()), ("version", pa.int64()), ("payload", pa.string())]),
            )
            con.register("incoming", incoming)
            try:
                con.execute("INSERT INTO records SELECT entity,id,version,payload FROM incoming ON CONFLICT(entity,id) DO UPDATE SET version=excluded.version,payload=excluded.payload")
            finally:
                con.unregister("incoming")
        if state(con) != candidate:
            raise RuntimeError("DATABASE_RECONCILIATION")
        evidence["reconciliation"]["active_rows"] = dict(con.execute((PROJECT / "sql" / "reconciliation.sql").read_text()).fetchall())
        evidence["processing_seconds"] = clock() - start
        evidence["database_seconds"] = clock() - stage
        con.execute("INSERT INTO runs VALUES (?,?,?)", [run_id, "committed", canonical(evidence)])
        fault(selected, "before_commit")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
