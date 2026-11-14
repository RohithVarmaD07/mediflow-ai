"""Typed Parquet generation from committed canonical state."""
import json
import os
from datetime import date
import pyarrow as pa
import pyarrow.parquet as pq
from .config import PROJECT, safe_path
from .evidence import atomic_json, file_hash
from .generate import ENTITIES
from .recovery import fault, retry

SCHEMAS = {
    "patients": pa.schema([("id", pa.string()), ("birth_date", pa.date32()), ("region", pa.string()), ("active", pa.bool_())]),
    "appointments": pa.schema([("id", pa.string()), ("patient_id", pa.string()), ("facility_code", pa.string()), ("scheduled_at", pa.timestamp("us", tz="UTC")), ("status", pa.string()), ("appointment_type", pa.string())]),
    "encounters": pa.schema([("id", pa.string()), ("patient_id", pa.string()), ("appointment_id", pa.string()), ("facility_code", pa.string()), ("start_at", pa.timestamp("us", tz="UTC")), ("end_at", pa.timestamp("us", tz="UTC")), ("encounter_type", pa.string())]),
}


def publish(con, root, run_id, selected=None):
    from .storage import state
    from .validation import timestamp
    snapshot = safe_path(root, root / "snapshots" / run_id)
    staging = safe_path(root, root / "staging" / run_id)
    outputs = {}
    if not snapshot.exists():
        staging.mkdir(parents=True, exist_ok=True)
        current = state(con)
        for entity in ENTITIES:
            schema = SCHEMAS[entity]
            rows = []
            for row in current[entity].values():
                if row["is_deleted"]:
                    continue
                value = {name: row[name] for name in schema.names}
                if entity == "patients":
                    value["birth_date"] = date.fromisoformat(value["birth_date"])
                else:
                    for name in ("scheduled_at",) if entity == "appointments" else ("start_at", "end_at"):
                        value[name] = timestamp(value[name])
                rows.append(value)
            table = pa.Table.from_pylist(rows, schema=schema)
            path = staging / f"{entity}.parquet"
            pq.write_table(table, path, compression="zstd")
            if not pq.read_table(path).equals(table):
                raise RuntimeError("PARQUET_ROUNDTRIP")
            outputs[path.name] = {"rows": len(rows), "sha256": file_hash(path)}
            fault(selected, "parquet_write")
        for name in ("patient_summary", "daily_appointments", "daily_encounters"):
            table = con.execute((PROJECT / "sql" / f"{name}.sql").read_text()).fetch_arrow_table()
            path = staging / f"{name}.parquet"
            pq.write_table(table, path, compression="zstd")
            outputs[path.name] = {"rows": table.num_rows, "sha256": file_hash(path)}
        atomic_json(staging / "outputs.json", outputs)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        retry(lambda: os.replace(staging, snapshot))
    else:
        outputs = json.loads((snapshot / "outputs.json").read_text())
    for name, info in outputs.items():
        if file_hash(snapshot / name) != info["sha256"]:
            raise RuntimeError("SNAPSHOT_HASH")
    fault(selected, "before_pointer")
    atomic_json(root / "current.json", {"snapshot_id": run_id, "outputs": outputs})
    fault(selected, "after_pointer")
    return outputs
