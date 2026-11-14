"""Seeded synthetic source generation with explicit source versions."""
from datetime import datetime, timedelta, timezone
import copy
import json
import random
from .config import budget, safe_path
from .evidence import atomic_json, canonical, file_hash

ENTITIES = ("patients", "appointments", "encounters")


def base(key, as_of):
    return {"id": key, "schema_version": "1.0.0", "source_system": "synthetic",
            "synthetic": True, "source_version": 1, "source_updated_at": as_of,
            "is_deleted": False}


def generate(seed=42, patients=1000, appointments=5000, as_of="2026-01-01T00:00:00Z"):
    if not 1 <= patients <= 10000 or not 1 <= appointments <= 50000:
        raise ValueError("GENERATION_LIMIT")
    rng = random.Random(seed)
    origin = datetime.fromisoformat(as_of.replace("Z", "+00:00")) - timedelta(days=30)
    rows = {e: [] for e in ENTITIES}
    for i in range(patients):
        row = base(f"P{i:06d}", as_of)
        row.update(birth_date=f"{rng.randint(1940, 2005)}-01-01", region=f"R{i % 5}", active=True)
        rows["patients"].append(row)
    for i in range(appointments):
        when = origin + timedelta(days=i % 30, minutes=i % 480)
        stamp = when.isoformat().replace("+00:00", "Z")
        status = "completed" if i % 10 < 8 else ("cancelled" if i % 10 == 8 else "missed")
        row = base(f"A{i:06d}", as_of)
        row.update(patient_id=f"P{i % patients:06d}", facility_code=f"F{i % 3}",
                   scheduled_at=stamp, status=status, appointment_type="routine")
        rows["appointments"].append(row)
        if status == "completed":
            encounter = base(f"E{i:06d}", as_of)
            encounter.update(patient_id=row["patient_id"], appointment_id=row["id"],
                             facility_code=row["facility_code"], start_at=stamp,
                             end_at=(when + timedelta(minutes=15 + i % 30)).isoformat().replace("+00:00", "Z"),
                             encounter_type="outpatient")
            rows["encounters"].append(encounter)
    return rows


def write_batch(root, name, rows, provenance=None):
    if not name.replace("-", "").replace("_", "").isalnum():
        raise ValueError("BATCH_NAME")
    budget()
    folder = safe_path(root, root / "source" / name)
    folder.mkdir(parents=True, exist_ok=False)
    files = {}
    for entity in ENTITIES:
        path = folder / f"{entity}.jsonl"
        with path.open("x", encoding="utf-8", newline="\n") as f:
            for row in rows.get(entity, []):
                f.write(canonical(row) + "\n")
        files[entity] = {"sha256": file_hash(path), "rows": len(rows.get(entity, []))}
    atomic_json(folder / "manifest.json", {"schema_version": "1.0.0", "files": files,
                                          "provenance": provenance or {}})
    return folder


def demo_batches(seed=42, patients=1000, appointments=5000, as_of="2026-01-01T00:00:00Z"):
    first = generate(seed, patients, appointments, as_of)
    corrections = {e: [] for e in ENTITIES}
    for entity in ("appointments", "encounters"):
        row = copy.deepcopy(first[entity][0])
        row["source_version"] = 2
        row["source_updated_at"] = "2026-03-01T00:00:00Z"
        field = "scheduled_at" if entity == "appointments" else "start_at"
        row[field] = "2025-12-15T10:00:00Z"
        if entity == "encounters":
            row["end_at"] = "2025-12-15T10:45:00Z"
        corrections[entity].append(row)
    bad = copy.deepcopy(first["patients"][0])
    bad["birth_date"] = "not-a-date"
    last = {"patients": [bad, first["patients"][1], first["patients"][1]],
            "appointments": [first["appointments"][0]], "encounters": []}
    return [first, corrections, last]
