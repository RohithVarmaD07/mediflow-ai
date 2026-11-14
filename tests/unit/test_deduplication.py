import copy
from mediflow.deduplicate import classify


def test_exact_duplicates(rows):
    row=rows['patients'][0]
    winners,counts,rejects=classify([('patients',1,'a',row),('patients',2,'a',row)], {e:{} for e in rows})
    assert counts['accepted']==1 and counts['duplicate']==1 and not rejects


def test_conflicting_payload(rows):
    row=rows['patients'][0]; other=copy.deepcopy(row); other['region']='R99'
    winners,counts,rejects=classify([('patients',1,'a',row),('patients',2,'a',other)],{e:{} for e in rows})
    assert not winners and counts['invalid']==2 and len(rejects)==2
