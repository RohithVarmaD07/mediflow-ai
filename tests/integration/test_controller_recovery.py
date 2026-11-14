import json
import os
import subprocess
import sys
import pytest
from mediflow.config import PROJECT, APPROVED
from mediflow.incremental import run
from mediflow.history import read_invocation, list_history


@pytest.mark.parametrize("point", ["after_commit", "parquet_write", "before_pointer", "after_pointer", "evidence"])
def test_recovery_stage_identity(root,batch,point):
    env=dict(os.environ,MEDIFLOW_TEST_FAULTS="1",PYTHONDONTWRITEBYTECODE="1")
    child=subprocess.run([sys.executable,"-B","-m","mediflow","run","--root",str(root),"--batch",str(batch),"--fault",point],cwd=PROJECT,env=env,capture_output=True,text=True,timeout=60)
    assert child.returncode==77,child.stderr
    result=run(root,batch)
    recovered=result["recovered_runs"][0]
    rows=read_invocation(result["invocation_id"])["records"]
    recovery=[r for r in rows if r["recovery_of_run_id"]==recovered]
    assert [r["stage_id"] for r in recovery if r["status"]=="succeeded"]==["publish","finalize"]
    assert result["counts"]["duplicate"]==64
    if point != "after_commit":
        assert next(r for r in recovery if r["stage_id"]=="publish")["attempt_number"]==2


@pytest.mark.parametrize("boundary", ["stage_start", "finalization_end"])
def test_controller_boundary_crashes(root,batch,boundary):
    code = """
import os,sys
from pathlib import Path
from mediflow import orchestration
from mediflow.incremental import run
original=orchestration.write_transition
def write(record):
    original(record)
    if (sys.argv[3]=='stage_start' and record['stage_id']=='ingest' and record['status']=='running') or (sys.argv[3]=='finalization_end' and record['stage_id']=='finalize' and record['status']=='succeeded'):
        os._exit(77)
orchestration.write_transition=write
run(Path(sys.argv[1]),Path(sys.argv[2]))
"""
    child=subprocess.run([sys.executable,"-B","-c",code,str(root),str(batch),boundary],cwd=PROJECT,capture_output=True,text=True,timeout=60)
    assert child.returncode==77,child.stderr
    result=run(root,batch)
    assert result["reconciliation"]["difference"]==0
    if boundary=="finalization_end": assert result["counts"]["duplicate"]==64
    items=list_history(root)["items"]
    assert len([i for i in items if "invocation_id" in i])==2
