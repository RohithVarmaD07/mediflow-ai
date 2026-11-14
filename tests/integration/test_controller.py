import json
import subprocess
import sys
import pytest
from mediflow import incremental
from mediflow.config import APPROVED, PROJECT
from mediflow.history import STAGES, read_invocation, list_history
from mediflow.evidence import file_hash


def test_pipeline_stages_and_cli_history(root, batch):
    result = incremental.run(root, batch)
    history = read_invocation(result["invocation_id"])
    assert not history["errors"]
    assert history["status"] == "succeeded"
    assert [r["stage_id"] for r in history["records"] if r["status"] == "succeeded"] == list(STAGES)
    before = {str(p): file_hash(p) for p in root.rglob("*") if p.is_file()}
    process = subprocess.run([sys.executable,"-B","-m","mediflow","history","--root",str(root)],cwd=PROJECT,capture_output=True,text=True,timeout=60)
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)["items"][0]["invocation_id"] == result["invocation_id"]
    assert before == {str(p): file_hash(p) for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("stage", ["ingest", "prepare", "commit", "publish", "finalize"])
def test_stage_failure_stops_dependencies(root, batch, monkeypatch, stage):
    names = {"ingest":"ingest", "prepare":"prepare_batch", "commit":"commit_candidate", "publish":"publish", "finalize":"finalize_evidence"}
    calls=[]
    def fail(*args, **kwargs): calls.append(1); raise ValueError("injected")
    monkeypatch.setattr(incremental,names[stage],fail)
    with pytest.raises(ValueError,match="injected"): incremental.run(root,batch)
    items=list_history(root)["items"]
    record=next(i for i in items if "records" in i)
    rows=record["records"]
    assert len(calls)==1
    assert any(r["stage_id"]==stage and r["status"]=="failed" for r in rows)
    later=STAGES[STAGES.index(stage)+1:]
    assert {r["stage_id"] for r in rows if r["status"]=="blocked"}==set(later)


def test_legacy_history(root):
    import uuid
    run_id=str(uuid.uuid4()); directory=root/"runs"/run_id
    directory.mkdir(parents=True)
    (directory/"manifest.json").write_text(json.dumps({"run_id":run_id,"status":"succeeded"}))
    item=list_history(root)["items"][0]
    assert item["status"]=="stage_history_unavailable"


def test_history_does_not_open_database(root,batch,monkeypatch):
    incremental.run(root,batch)
    import duckdb
    monkeypatch.setattr(duckdb,"connect",lambda *a,**k:pytest.fail("history opened database"))
    assert list_history(root)["items"]
