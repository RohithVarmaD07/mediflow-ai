import copy
import json
from mediflow.generate import write_batch
from mediflow.incremental import run


def test_invalid_then_corrected(root,rows):
    bad=copy.deepcopy(rows['patients'][0]); bad['birth_date']='bad'
    result=run(root,write_batch(root,'bad',{'patients':[bad]}))
    assert result['counts']['invalid']==1
    rejected=json.loads((root/'runs'/result['run_id']/'quarantine.jsonl').read_text())
    assert rejected['source_sha256'] and rejected['reason']=='VALUE'
    fixed=run(root,write_batch(root,'fixed',{'patients':[rows['patients'][0]]}))
    assert fixed['changes']['inserts']==1


def test_orphan_batch_quarantined(root,rows):
    result=run(root,write_batch(root,'orphans',{'appointments':[rows['appointments'][0]]}))
    assert result['counts']['invalid']==1 and result['counts']['accepted']==0
