"""Milestone 1 startup, invariant, and recovery compatibility safeguards."""
import copy
import json
import pytest
from mediflow import incremental
from mediflow.config import APPROVED
from mediflow.evidence import canonical
from mediflow.storage import connect, state


def invocation_after(before):
    paths = set((APPROVED / "invocations").glob("*.json")) - before
    assert len(paths) == 1
    return json.loads(paths.pop().read_text())


@pytest.mark.parametrize("target,stage", [("budget", "storage"), ("runtime", "storage"),
    ("writer_lock", "lock"), ("connect", "database"), ("recover", "recovery")])
def test_startup_failures(root, batch, monkeypatch, target, stage):
    before = set((APPROVED / "invocations").glob("*.json"))
    def fail(*args, **kwargs):
        raise RuntimeError("INJECTED_STARTUP_FAILURE")
    monkeypatch.setattr(incremental, target, fail)
    with pytest.raises(RuntimeError, match="INJECTED_STARTUP_FAILURE"):
        incremental.run(root, batch)
    outcome = invocation_after(before)
    assert outcome["status"] == "startup_failed" and outcome["stage"] == stage
    assert outcome["finished_at"] and outcome["invocation_id"]
    assert not (root / "runs").exists()


def test_real_lock_failure(root, batch):
    from mediflow.recovery import writer_lock
    before = set((APPROVED / "invocations").glob("*.json"))
    with writer_lock(root):
        with pytest.raises(RuntimeError, match="WRITER_BUSY"):
            incremental.run(root, batch)
    assert invocation_after(before)["stage"] == "lock"


def test_invocation_link(root, batch):
    result = incremental.run(root, batch)
    outcome = json.loads((APPROVED / "invocations" / (result["invocation_id"] + ".json")).read_text())
    assert outcome["status"] == "succeeded" and outcome["run_id"] == result["run_id"]


@pytest.mark.parametrize("kind", ["implementation", "sql", "schema", "configuration", "dependency", "legacy"])
def test_incompatible_recovery(root, batch, monkeypatch, kind):
    original_finish = incremental.finish
    def fail(*args, **kwargs):
        raise RuntimeError("PUBLICATION_INTERRUPTED")
    monkeypatch.setattr(incremental, "finish", fail)
    with pytest.raises(RuntimeError, match="PUBLICATION_INTERRUPTED"):
        incremental.run(root, batch)
    monkeypatch.setattr(incremental, "finish", original_finish)
    con = connect(root)
    before_state = state(con)
    run_id, payload = con.execute("SELECT run_id,evidence FROM runs WHERE status='committed'").fetchone()
    saved = json.loads(payload)
    changed = copy.deepcopy(saved)
    if kind == "legacy":
        changed.pop("compatibility")
    elif kind == "dependency":
        changed["compatibility"]["dependencies"]["duckdb"] = "different"
    else:
        prefixes = {"implementation": "mediflow/", "sql": "sql/daily_", "schema": "sql/schema", "configuration": "config/"}
        key = next(k for k in changed["compatibility"]["files"] if k.startswith(prefixes[kind]))
        changed["compatibility"]["files"][key] = "different"
    con.execute("UPDATE runs SET evidence=? WHERE run_id=?", [canonical(changed), run_id])
    with pytest.raises(RuntimeError, match="INCOMPATIBLE_RECOVERY"):
        incremental.recover(con, root)
    assert state(con) == before_state
    assert not (root / "current.json").exists()
    con.close()
    with pytest.raises(RuntimeError, match="INCOMPATIBLE_RECOVERY"):
        incremental.run(root, batch)
    # Restore the matching fingerprint only in this controlled test database.
    import duckdb
    con = duckdb.connect(str(root / "state" / "mediflow.duckdb"))
    assert con.execute("SELECT status FROM runs WHERE run_id=?", [run_id]).fetchone()[0] == "committed"
    con.execute("UPDATE runs SET evidence=? WHERE run_id=?", [canonical(saved), run_id])
    con.close()
    replay = incremental.run(root, batch)
    assert replay["recovered_runs"] == [run_id]
    assert replay["counts"]["accepted"] == 0


@pytest.mark.parametrize("kind", ["relationships", "accounting"])
def test_explicit_invariants(root, batch, monkeypatch, kind):
    if kind == "relationships":
        monkeypatch.setattr(incremental, "relationship_errors", lambda candidate: ["invalid"])
        code = "RELATIONSHIP_INVARIANT"
    else:
        original = incremental.classify
        def broken(*args):
            winners, counts, conflicts = original(*args)
            counts["accepted"] += 1
            return winners, counts, conflicts
        monkeypatch.setattr(incremental, "classify", broken)
        code = "ROW_ACCOUNTING_INVARIANT"
    with pytest.raises(RuntimeError, match=code):
        incremental.run(root, batch)
    con = connect(root)
    assert all(not rows for rows in state(con).values())
    assert con.execute("SELECT count(*) FROM runs").fetchone()[0] == 0
    con.close()


@pytest.mark.parametrize("kind", ["relationships", "accounting"])
def test_invariants_under_optimized_python(root, batch, kind):
    import subprocess
    import sys
    from mediflow.config import PROJECT
    code = """
import sys
from pathlib import Path
from mediflow import incremental
kind = sys.argv[3]
if kind == 'relationships':
    incremental.relationship_errors = lambda candidate: ['invalid']
    expected = 'RELATIONSHIP_INVARIANT'
else:
    original = incremental.classify
    def broken(*args):
        winners, counts, conflicts = original(*args)
        counts['accepted'] += 1
        return winners, counts, conflicts
    incremental.classify = broken
    expected = 'ROW_ACCOUNTING_INVARIANT'
try:
    incremental.run(Path(sys.argv[1]), Path(sys.argv[2]))
except RuntimeError as exc:
    sys.exit(0 if str(exc) == expected else 2)
sys.exit(3)
"""
    result = subprocess.run([sys.executable, "-B", "-O", "-c", code, str(root), str(batch), kind],
                            cwd=PROJECT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr


def test_rejected_path_has_evidence(root, batch):
    before = set((APPROVED / "invocations").glob("*.json"))
    with pytest.raises(ValueError, match="PATH_OUTSIDE_ROOT"):
        incremental.run(APPROVED.parent / "unapproved", batch)
    outcome = invocation_after(before)
    assert outcome["status"] == "startup_failed" and outcome["stage"] == "storage"


def test_evidence_failure_preserves_original_error(root, batch, monkeypatch):
    original = incremental.atomic_json
    def write(path, value):
        if value.get("status") == "startup_failed":
            raise PermissionError("evidence unavailable")
        original(path, value)
    def fail(*args):
        raise RuntimeError("STORAGE_BUDGET")
    monkeypatch.setattr(incremental, "atomic_json", write)
    monkeypatch.setattr(incremental, "budget", fail)
    with pytest.raises(RuntimeError, match="STORAGE_BUDGET") as caught:
        incremental.run(root, batch)
    assert "Invocation outcome could not be persisted" in caught.value.__notes__[0]

