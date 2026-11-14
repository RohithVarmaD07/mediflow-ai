import copy
import pyarrow.parquet as pq
from mediflow.generate import write_batch
from mediflow.incremental import run


def test_late_update_moves_date(root,batch,rows):
    run(root,batch)
    corrected=copy.deepcopy(rows['encounters'][0]); corrected.update(source_version=2,start_at='2020-01-01T00:00:00Z',end_at='2020-01-01T01:00:00Z')
    result=run(root,write_batch(root,'late',{'encounters':[corrected]}))
    table=pq.read_table(root/'snapshots'/result['run_id']/'daily_encounters.parquet').to_pylist()
    moved=[r for r in table if str(r['day'])=='2020-01-01']
    assert len(moved)==1 and moved[0]['duration_seconds']==3600
    assert result['changes']['updates']==1
