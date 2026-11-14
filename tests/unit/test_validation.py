import copy
import pytest
from mediflow.validation import validate, relationship_errors


def test_generated_contract(rows):
    for entity, records in rows.items():
        assert all(validate(entity, r) is None for r in records)
    assert not relationship_errors({e: {r["id"]: r for r in rs} for e, rs in rows.items()})


@pytest.mark.parametrize('field,value', [('birth_date','bad'),('source_version',True),('source_version',0),('synthetic',False),('id','../bad'),('active','yes'),('source_updated_at','2026-01-01')])
def test_invalid_patient(rows, field, value):
    row=copy.deepcopy(rows['patients'][0]); row[field]=value
    assert validate('patients',row) is not None


def test_reverse_encounter(rows):
    row=copy.deepcopy(rows['encounters'][0]); row['end_at']='2000-01-01T00:00:00Z'
    assert validate('encounters',row)=='TIME_ORDER'
