"""Explicit source contract validation; no executable schema expressions."""
from datetime import date, datetime
import re

COMMON = {"id", "schema_version", "source_system", "synthetic", "source_version", "source_updated_at", "is_deleted"}
FIELDS = {
    "patients": {"birth_date", "region", "active"},
    "appointments": {"patient_id", "facility_code", "scheduled_at", "status", "appointment_type"},
    "encounters": {"patient_id", "appointment_id", "facility_code", "start_at", "end_at", "encounter_type"},
}


def timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("UTC_REQUIRED")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(entity, row):
    try:
        if not isinstance(row, dict) or set(row) != COMMON | FIELDS[entity]:
            return "FIELDS"
        if row["synthetic"] is not True or row["schema_version"] != "1.0.0" or row["source_system"] != "synthetic":
            return "CONTRACT"
        if type(row["source_version"]) is not int or not 1 <= row["source_version"] <= 1000000:
            return "VERSION"
        if type(row["is_deleted"]) is not bool:
            return "BOOLEAN"
        for key, value in row.items():
            if isinstance(value, str) and len(value) > 100:
                return "STRING_LIMIT"
            if key == "id" or key.endswith("_id"):
                if key == "appointment_id" and value is None:
                    continue
                if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Za-z0-9_-]{1,63}", value):
                    return "IDENTIFIER"
        updated = timestamp(row["source_updated_at"])
        if entity == "patients":
            if type(row["active"]) is not bool or not isinstance(row["region"], str):
                return "TYPE"
            if date.fromisoformat(row["birth_date"]) > updated.date():
                return "BIRTH_DATE"
        elif entity == "appointments":
            timestamp(row["scheduled_at"])
            if row["status"] not in {"scheduled", "completed", "cancelled", "missed"}:
                return "STATUS"
            if row["appointment_type"] not in {"routine", "urgent"}:
                return "CODE"
        else:
            if timestamp(row["end_at"]) < timestamp(row["start_at"]):
                return "TIME_ORDER"
            if row["encounter_type"] not in {"outpatient", "walk_in"}:
                return "CODE"
        if entity != "patients" and not isinstance(row["facility_code"], str):
            return "TYPE"
    except (ValueError, TypeError, KeyError, OverflowError):
        return "VALUE"
    return None


def relationship_errors(state):
    errors = set()
    active = {e: {k: r for k, r in rows.items() if not r["is_deleted"]} for e, rows in state.items()}
    for entity in ("appointments", "encounters"):
        for key, row in active[entity].items():
            if row["patient_id"] not in active["patients"]:
                errors.add((entity, key))
            if entity == "encounters" and row["appointment_id"] is not None:
                appointment = active["appointments"].get(row["appointment_id"])
                if not appointment or appointment["patient_id"] != row["patient_id"] or appointment["status"] != "completed":
                    errors.add((entity, key))
    return errors
