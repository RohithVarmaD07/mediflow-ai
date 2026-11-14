import json
from mediflow.evidence import atomic_json, digest, event


def test_atomic_evidence(root):
    path=root/'manifest.json'
    atomic_json(path,{'status':'started'}); atomic_json(path,{'status':'done'})
    assert json.loads(path.read_text())=={'status':'done'}
    assert not path.with_suffix('.json.tmp').exists()
    event(root,'done')
    assert json.loads((root/'events.jsonl').read_text())['state']=='done'


def test_digest_order_independent():
    assert digest({'a':1,'b':2})==digest({'b':2,'a':1})
