import copy
from mediflow.deduplicate import classify


def test_highest_source_version_wins(rows):
    old=rows['patients'][0]; new=copy.deepcopy(old); new['source_version']=3
    winners,counts,_=classify([('patients',1,'a',new),('patients',2,'a',old)],{e:{} for e in rows})
    assert next(iter(winners.values()))[3]['source_version']==3
    assert counts['superseded']==1


def test_stale_cannot_overwrite(rows):
    old=rows['patients'][0]; new=copy.deepcopy(old); new['source_version']=2
    existing={e:{} for e in rows}; existing['patients'][new['id']]=new
    winners,counts,_=classify([('patients',1,'a',old)],existing)
    assert not winners and counts['stale']==1
