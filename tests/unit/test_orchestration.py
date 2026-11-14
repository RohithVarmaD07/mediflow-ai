import uuid
import pytest
from mediflow.orchestration import ExecutionContext, SequentialController
from mediflow.history import STAGES, read_invocation
from mediflow.recovery import retry


def controller():
    return SequentialController(ExecutionContext(str(uuid.uuid4()), None))


def test_sequence_and_return_values():
    c = controller()
    for stage in STAGES:
        assert c.execute_stage(stage, lambda: 7) == 7
    records = read_invocation(c.context.invocation_id)["records"]
    assert [r["stage_id"] for r in records if r["status"] == "running"] == list(STAGES)
    assert [r["sequence"] for r in records] == list(range(1, 19))


def test_dependency_and_duplicate_prevention():
    c = controller()
    with pytest.raises(RuntimeError, match="STAGE_DEPENDENCY"):
        c.execute_stage("commit", lambda: pytest.fail("must not run"))
    c.execute_stage("startup", lambda: None)
    with pytest.raises(RuntimeError, match="STAGE_TRANSITION"):
        c.execute_stage("startup", lambda: pytest.fail("must not repeat"))


def test_failure_blocks_dependents():
    c = controller()
    def fail(): raise ValueError("private payload")
    with pytest.raises(ValueError): c.execute_stage("startup", fail)
    rows = read_invocation(c.context.invocation_id)["records"]
    assert rows[1]["status"] == "failed"
    assert all(r["status"] == "blocked" for r in rows[2:])
    assert "private payload" not in str(rows)


@pytest.mark.parametrize("success", [True, False])
def test_operation_retries_not_multiplied(success):
    c = controller(); calls = []
    def operation():
        calls.append(1)
        if not success or len(calls) < 3: raise PermissionError("sharing")
        return 1
    if success:
        assert c.execute_stage("startup", lambda: retry(operation, delays=(0, 0))) == 1
    else:
        with pytest.raises(PermissionError): c.execute_stage("startup", lambda: retry(operation, delays=(0, 0)))
    assert len(calls) == 3


def test_record_failure_preserves_original(monkeypatch):
    c = controller()
    from mediflow import orchestration
    original = orchestration.write_transition
    def write(record):
        if record["status"] == "failed": raise OSError("disk")
        original(record)
    monkeypatch.setattr(orchestration, "write_transition", write)
    def fail(): raise RuntimeError("original")
    with pytest.raises(RuntimeError, match="original") as exc: c.execute_stage("startup", fail)
    assert exc.value.__notes__
