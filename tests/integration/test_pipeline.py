import json
import pyarrow.parquet as pq
from mediflow.incremental import run


def test_end_to_end(root,batch):
    report=run(root,batch)
    assert report['counts']['accepted']==64
    assert report['reconciliation']['difference']==0
    snapshot=root/'snapshots'/report['run_id']
    assert pq.read_table(snapshot/'patients.parquet').num_rows==10
    assert pq.read_table(snapshot/'appointments.parquet').num_rows==30
    assert pq.read_table(snapshot/'encounters.parquet').num_rows==24
    for name in ['manifest.json','events.jsonl','metrics.json','quality.json','reconciliation.json','outputs.json','quarantine.jsonl']:
        assert (root/'runs'/report['run_id']/name).exists()


def test_replay_is_idempotent(root,batch):
    first=run(root,batch); second=run(root,batch)
    assert second['counts']['duplicate']==64 and second['counts']['accepted']==0
    assert first['reconciliation']['canonical_digest']==second['reconciliation']['canonical_digest']
    assert first['outputs']==second['outputs']
