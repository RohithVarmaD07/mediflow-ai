# Phase 2 data model

Patients, appointments, and encounters are synthetic source entities keyed by `id` within each entity type. Each source record has `source_version`, `source_updated_at`, `source_system`, `schema_version`, `synthetic`, and `is_deleted`. DuckDB stores canonical keyed JSON plus version, retaining tombstones. SQL views expose active typed records. Source timestamps, business timestamps, and ingestion/run time are separate.

An appointment belongs to one patient. An encounter belongs to one patient and optionally one completed appointment belonging to that same patient. Null appointment links permit walk-ins. Phase 2 permits multiple encounters per appointment, so analytical joins must respect grain. Patient summaries aggregate appointments and encounters independently before joining.

Parquet entity outputs include active business fields; raw input and canonical DuckDB payloads retain full version provenance. Three analytical outputs are `patient_summary`, `daily_appointments`, and `daily_encounters`. No-show denominator is completed plus missed appointments; cancelled and still-scheduled appointments are excluded. Zero denominators produce NULL.

Providers, detailed clinical observations, procedures, slowly changing dimensions, and clinical vocabulary conformance are deferred. Facility and region values are synthetic codes. See the [dictionary](data-dictionary.md) and [incremental policy](incremental-processing.md).
