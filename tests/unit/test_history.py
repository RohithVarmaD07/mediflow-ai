import json
import uuid
import pytest
from mediflow.config import APPROVED
from mediflow.history import read_invocation, validate_record, write_transition, list_history
from mediflow.orchestration import ExecutionContext, SequentialController


def sample():
    c = SequentialController(ExecutionContext(str(uuid.uuid4()), None))
    c.execute_stage("startup", lambda: None)
    return read_invocation(c.context.invocation_id)["records"][0]


@pytest.mark.parametrize("field,value", [("schema_version","2"), ("sequence",0),
    ("sequence",True), ("attempt_id","bad"), ("elapsed_seconds",-1),
    ("root_ref","../escape"), ("evidence_refs",["C:/secret"]),
    ("error_code","secret text"), ("stage_id","arbitrary"), ("status","unknown")])
def test_invalid_records(field, value):
    record = sample(); record[field] = value
    with pytest.raises(ValueError): validate_record(record)


def test_existing_record_cannot_be_overwritten():
    record = sample()
    with pytest.raises(ValueError, match="HISTORY_OVERWRITE"): write_transition(record)


@pytest.mark.parametrize("kind", ["truncated", "duplicate_sequence", "oversized", "partial", "terminal_rewrite"])
def test_corrupted_history_visible(kind):
    record = sample()
    directory = APPROVED / "invocations" / record["invocation_id"] / "controller"
    path = directory / "0002.json"
    if kind == "truncated": path.write_text('{')
    elif kind == "oversized": path.write_text(' ' * 8193)
    elif kind == "partial": (directory / "0003.json.tmp").write_text('{}')
    elif kind == "terminal_rewrite":
        terminal = json.loads(path.read_text()); terminal["sequence"] = 3
        (directory / "0003.json").write_text(json.dumps(terminal))
    else:
        record["sequence"] = 1; path.write_text(json.dumps(record))
    result = read_invocation(record["invocation_id"])
    assert result["status"] == "corrupt" and result["errors"]


def test_incomplete_attempt_is_not_live_or_successful():
    c = SequentialController(ExecutionContext(str(uuid.uuid4()), None))
    from mediflow.orchestration import StageAttempt
    c.record(StageAttempt("startup", str(uuid.uuid4()), 1), "running")
    assert read_invocation(c.context.invocation_id)["status"] == "completion_not_recorded"


def test_history_does_not_create_paths(root):
    missing = root / "not-created"
    assert list_history(missing)["items"] == []
    assert not missing.exists()
    with pytest.raises(ValueError): list_history(root, 0)


@pytest.mark.parametrize("field,value", [("sequence",65), ("root_ref","x"*241), ("evidence_refs",["x"]*11)])
def test_record_limits(field,value):
    record=sample(); record[field]=value
    with pytest.raises(ValueError): validate_record(record)


def test_missing_outcome_does_not_claim_success():
    from mediflow.history import STAGES
    c=SequentialController(ExecutionContext(str(uuid.uuid4()),None))
    for stage in STAGES: c.execute_stage(stage,lambda:None)
    assert read_invocation(c.context.invocation_id)["status"]=="completion_not_recorded"


def test_forged_dependency_order_rejected():
    record=sample(); record["stage_id"]="commit"
    directory=APPROVED/"invocations"/record["invocation_id"]/"controller"
    (directory/"0001.json").write_text(json.dumps(record))
    assert read_invocation(record["invocation_id"])["status"]=="corrupt"


def test_result_limit_is_explicit(root):
    for _ in range(2):
        run_id=str(uuid.uuid4()); directory=root/"runs"/run_id; directory.mkdir(parents=True)
        (directory/"manifest.json").write_text(json.dumps({"run_id":run_id,"status":"succeeded"}))
    result=list_history(root,1)
    assert len(result["items"])==1 and result["truncated"]



def test_foreign_corrupt_history_not_attributed_to_pipeline(root):
    record=sample()
    record["stage_id"]="commit"  # Invalid order, but root_ref identifies another context.
    path=APPROVED/"invocations"/record["invocation_id"]/"controller"/"0001.json"
    path.write_text(json.dumps(record))
    result=list_history(root)
    assert result["items"]==[] and result["errors"]==[]
    assert record["invocation_id"] not in str(result["unattributed_errors"])


def test_local_corrupt_history_remains_visible(root):
    c=SequentialController(ExecutionContext(str(uuid.uuid4()),root.relative_to(APPROVED).as_posix()))
    c.execute_stage("startup",lambda:None)
    path=APPROVED/"invocations"/c.context.invocation_id/"controller"/"0002.json"
    path.write_text('{')
    result=list_history(root)
    assert result["items"][0]["status"]=="corrupt"
    assert result["errors"] and not result["items"][0]["records"][-1]["status"]=="succeeded"
