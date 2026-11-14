"""Independent full-history and complete analytical-result comparisons."""
from collections import Counter
from datetime import datetime, timezone
import copy
import random

import pytest
import pyarrow.parquet as pq

from mediflow.generate import generate, write_batch
from mediflow.incremental import run
from mediflow.storage import connect, state

KEYS = {
    "daily_appointments": ("day", "facility_code"),
    "daily_encounters": ("day", "facility_code"),
    "patient_summary": ("patient_id",),
}


def full_rebuild(history):
    """Resolve valid source history without production classification/merge code."""
    rebuilt = {entity: {} for entity in ("patients", "appointments", "encounters")}
    for entity in rebuilt:
        keys = {row["id"] for batch in history for row in batch.get(entity, [])}
        for key in keys:
            versions = [row for batch in history for row in batch.get(entity, []) if row["id"] == key]
            rebuilt[entity][key] = max(versions, key=lambda row: row["source_version"])
    return rebuilt


def utc_date(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc).date()


def expected_analytics(rebuilt):
    """Aggregate Python records independently of the production SQL."""
    active = {entity: [row for row in records.values() if not row["is_deleted"]]
              for entity, records in rebuilt.items()}
    appointments = {}
    for row in active["appointments"]:
        key = (utc_date(row["scheduled_at"]), row["facility_code"])
        group = appointments.setdefault(key, {"day": key[0], "facility_code": key[1],
            "appointments": 0, "completed": 0, "cancelled": 0, "missed": 0, "eligible": 0})
        group["appointments"] += 1
        if row["status"] in ("completed", "cancelled", "missed"):
            group[row["status"]] += 1
        group["eligible"] += row["status"] in ("completed", "missed")
    for group in appointments.values():
        group["no_show_rate"] = group["missed"] / group["eligible"] if group["eligible"] else None
    encounters = {}
    for row in active["encounters"]:
        key = (utc_date(row["start_at"]), row["facility_code"])
        group = encounters.setdefault(key, {"day": key[0], "facility_code": key[1],
                                            "encounters": 0, "duration_seconds": 0})
        group["encounters"] += 1
        group["duration_seconds"] += int((datetime.fromisoformat(row["end_at"]) -
                                         datetime.fromisoformat(row["start_at"])).total_seconds())
    appointment_counts = Counter(row["patient_id"] for row in active["appointments"])
    encounter_counts = Counter(row["patient_id"] for row in active["encounters"])
    patients = [{"patient_id": row["id"], "appointments": appointment_counts[row["id"]],
                 "encounters": encounter_counts[row["id"]]} for row in active["patients"]]
    return {"daily_appointments": list(appointments.values()),
            "daily_encounters": list(encounters.values()), "patient_summary": patients}


def assert_complete(actual, expected, columns):
    """Check duplicate keys before indexing, exact key sets, then every metric."""
    actual_keys = [tuple(row[column] for column in columns) for row in actual]
    expected_keys = [tuple(row[column] for column in columns) for row in expected]
    assert len(actual_keys) == len(set(actual_keys)), "Duplicate analytical group keys"
    assert len(expected_keys) == len(set(expected_keys)), "Invalid oracle: duplicate keys"
    missing, unexpected = set(expected_keys) - set(actual_keys), set(actual_keys) - set(expected_keys)
    assert not missing and not unexpected, f"Analytical group mismatch: missing={missing}, unexpected={unexpected}"
    expected_by_key = dict(zip(expected_keys, expected))
    for key, row in zip(actual_keys, actual):
        assert row == expected_by_key[key], f"Analytical metrics differ for {key}"


def verify_snapshot(root, result, history):
    expected = full_rebuild(history)
    con = connect(root)
    try:
        assert state(con) == expected
    finally:
        con.close()
    snapshot = root / "snapshots" / result["run_id"]
    for entity, records in expected.items():
        ids = pq.read_table(snapshot / f"{entity}.parquet")["id"].to_pylist()
        assert len(ids) == len(set(ids)), f"Duplicate {entity} ids"
        assert set(ids) == {key for key, row in records.items() if not row["is_deleted"]}
    for name, expected_rows in expected_analytics(expected).items():
        actual = pq.read_table(snapshot / f"{name}.parquet").to_pylist()
        assert_complete(actual, expected_rows, KEYS[name])


@pytest.mark.parametrize("seed", [1, 7, 42, 99])
def test_incremental_matches_independent_rebuild(root, seed):
    initial = generate(seed, 10, 30)
    changes = {entity: [] for entity in initial}
    for entity in ("appointments", "encounters"):
        row = copy.deepcopy(initial[entity][0])
        row["source_version"] = 2
        field = "scheduled_at" if entity == "appointments" else "start_at"
        row[field] = "2025-12-01T08:00:00Z"
        if entity == "encounters":
            row["end_at"] = "2025-12-01T09:00:00Z"
        changes[entity].append(row)
    new_patient = copy.deepcopy(initial["patients"][0])
    new_patient["id"] = "PNEW"
    changes["patients"].append(new_patient)
    deleted = copy.deepcopy(initial["appointments"][8])
    deleted.update(source_version=2, is_deleted=True)
    changes["appointments"].append(deleted)
    history = []
    for i, source in enumerate((initial, changes, initial)):
        rows = copy.deepcopy(source)
        for records in rows.values():
            random.Random(seed + i).shuffle(records)
        history.append(rows)
        result = run(root, write_batch(root, f"b{i}", rows))
        verify_snapshot(root, result, history)


def test_status_walk_in_deletion_and_late_correction_groups(root):
    initial = generate(42, 3, 10)
    unused = copy.deepcopy(initial["patients"][0])
    unused["id"] = "PUNUSED"
    initial["patients"].append(unused)
    initial["appointments"][8]["facility_code"] = "FCANCELONLY"
    walk_in = copy.deepcopy(initial["encounters"][0])
    walk_in.update(id="EWALK", appointment_id=None, encounter_type="walk_in",
                   facility_code="FWALKONLY", patient_id=initial["patients"][2]["id"])
    initial["encounters"].extend([walk_in, copy.deepcopy(walk_in)])
    initial["appointments"].append(copy.deepcopy(initial["appointments"][1]))
    history = [initial]
    result = run(root, write_batch(root, "edge-baseline", initial))
    assert result["counts"]["duplicate"] == 2
    verify_snapshot(root, result, history)

    changes = {entity: [] for entity in initial}
    for entity in ("appointments", "encounters"):
        row = copy.deepcopy(initial[entity][0])
        row.update(source_version=2, source_updated_at="2026-03-01T00:00:00Z", facility_code="FLATE")
        if entity == "appointments":
            row["scheduled_at"] = "2020-01-01T10:00:00Z"
        else:
            row.update(start_at="2020-01-01T10:00:00Z", end_at="2020-01-01T11:00:00Z")
        changes[entity].append(row)
    cancelled = copy.deepcopy(initial["appointments"][8])
    cancelled.update(source_version=2, is_deleted=True)
    changes["appointments"].append(cancelled)
    corrected_no_show = copy.deepcopy(initial["appointments"][9])
    corrected_no_show.update(source_version=2, status="cancelled")
    changes["appointments"].append(corrected_no_show)
    deleted_walk_in = copy.deepcopy(walk_in)
    deleted_walk_in.update(source_version=2, is_deleted=True)
    changes["encounters"].append(deleted_walk_in)
    history.append(changes)
    result = run(root, write_batch(root, "edge-corrections", changes))
    assert result["changes"] == {"inserts": 0, "updates": 3, "tombstones": 2}
    verify_snapshot(root, result, history)
    replay = run(root, root / "source" / "edge-baseline")
    assert replay["changes"] == {"inserts": 0, "updates": 0, "tombstones": 0}
    verify_snapshot(root, replay, history + [initial])
    assert replay["outputs"] == result["outputs"]


@pytest.mark.parametrize("name", list(KEYS))
@pytest.mark.parametrize("mutation", ["missing", "unexpected", "duplicate", "empty"])
def test_oracle_rejects_incomplete_group_sets(name, mutation):
    expected = expected_analytics(full_rebuild([generate(42, 3, 10)]))[name]
    actual = copy.deepcopy(expected)
    if mutation == "missing":
        actual.pop()
    elif mutation == "empty":
        actual.clear()
    elif mutation == "duplicate":
        actual.append(copy.deepcopy(actual[0]))
    else:
        extra = copy.deepcopy(actual[0])
        extra[KEYS[name][-1]] = "UNEXPECTED"
        actual.append(extra)
    with pytest.raises(AssertionError, match="(Duplicate analytical|Analytical group mismatch)"):
        assert_complete(actual, expected, KEYS[name])


@pytest.mark.parametrize("name,metric", [
    ("daily_appointments", metric) for metric in
    ("appointments", "completed", "cancelled", "missed", "eligible", "no_show_rate")
] + [("daily_encounters", "encounters"), ("daily_encounters", "duration_seconds"),
     ("patient_summary", "appointments"), ("patient_summary", "encounters")])
def test_oracle_rejects_incorrect_metrics(name, metric):
    expected = expected_analytics(full_rebuild([generate(42, 3, 10)]))[name]
    actual = copy.deepcopy(expected)
    actual[0][metric] = (actual[0][metric] or 0) + 1
    with pytest.raises(AssertionError, match="Analytical metrics differ"):
        assert_complete(actual, expected, KEYS[name])


@pytest.mark.parametrize("name", list(KEYS))
def test_empty_history_has_no_analytical_groups(root, name):
    history = [{"patients": [], "appointments": [], "encounters": []}]
    result = run(root, write_batch(root, "empty", history[0]))
    verify_snapshot(root, result, history)
    assert pq.read_table(root / "snapshots" / result["run_id"] / f"{name}.parquet").num_rows == 0
