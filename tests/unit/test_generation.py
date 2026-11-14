from mediflow.generate import generate
from mediflow.evidence import digest
from datetime import datetime


def test_reproducible():
    assert digest(generate(42, 10, 30)) == digest(generate(42, 10, 30))
    assert digest(generate(42, 10, 30)) != digest(generate(43, 10, 30))


def test_grains(rows):
    assert {k: len(v) for k, v in rows.items()} == {"patients": 10, "appointments": 30, "encounters": 24}
    for entity in rows.values():
        assert len({r["id"] for r in entity}) == len(entity)
    assert all(datetime.fromisoformat(r['end_at']) <= datetime.fromisoformat(r['source_updated_at']) for r in rows['encounters'])
