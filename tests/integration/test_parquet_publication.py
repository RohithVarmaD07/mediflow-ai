import json
import pytest
from mediflow.evidence import file_hash
from mediflow.incremental import run


def test_snapshot_hashes(root,batch):
    report=run(root,batch)
    pointer=json.loads((root/'current.json').read_text())
    assert pointer['snapshot_id']==report['run_id']
    for name,info in pointer['outputs'].items():
        assert file_hash(root/'snapshots'/report['run_id']/name)==info['sha256']


def test_source_tampering(root,batch):
    with (batch/'patients.jsonl').open('a') as f: f.write('{}\n')
    with pytest.raises(ValueError,match='SOURCE_HASH'): run(root,batch)
    manifest=next((root/'runs').glob('*/manifest.json'))
    assert json.loads(manifest.read_text())['status']=='failed'
    assert json.loads((manifest.parent/'metrics.json').read_text())['elapsed_seconds'] >= 0
    assert json.loads((manifest.parent/'quality.json').read_text())['status']=='not_completed'
