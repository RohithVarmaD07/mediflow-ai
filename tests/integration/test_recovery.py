import json
import os
import subprocess
import sys
import pytest
from mediflow.config import PROJECT
from mediflow.incremental import run
from mediflow.recovery import retry, writer_lock


@pytest.mark.parametrize('point',['raw_copy','before_commit','after_commit','parquet_write','before_pointer','after_pointer','evidence'])
def test_crash_recovery(root,batch,point):
    env=dict(os.environ,MEDIFLOW_TEST_FAULTS='1',PYTHONDONTWRITEBYTECODE='1')
    child=subprocess.run([sys.executable,'-B','-m','mediflow','run','--root',str(root),'--batch',str(batch),'--fault',point],cwd=PROJECT,env=env,capture_output=True,text=True,timeout=60)
    assert child.returncode==77,child.stderr
    result=run(root,batch)
    assert result['reconciliation']['after']=={'patients':10,'appointments':30,'encounters':24}
    assert result['reconciliation']['difference']==0
    if point not in ('raw_copy','before_commit'):
        assert result['counts']['duplicate']==64 and result['recovered_runs']
    statuses=[json.loads(p.read_text())['status'] for p in (root/'runs').glob('*/manifest.json')]
    assert all(s in ('succeeded','interrupted_before_commit') for s in statuses)


def test_writer_exclusion(root):
    with writer_lock(root):
        with pytest.raises(RuntimeError,match='WRITER_BUSY'):
            with writer_lock(root): pass


def test_transient_retry():
    calls=[]
    def operation():
        calls.append(1)
        if len(calls)<3: raise PermissionError('sharing')
        return 'ok'
    assert retry(operation,delays=(0,0))=='ok' and len(calls)==3


def test_retry_exhaustion():
    calls=[]
    def operation():
        calls.append(1); raise PermissionError('sharing')
    with pytest.raises(PermissionError): retry(operation,delays=(0,0))
    assert len(calls)==3
