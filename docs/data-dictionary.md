# Source and analytical dictionary

| Entity | Fields beyond common envelope | Meaning |
| --- | --- | --- |
| patients | birth_date, region, active | ISO calendar date, synthetic region code, boolean active flag |
| appointments | patient_id, facility_code, scheduled_at, status, appointment_type | UTC schedule; scheduled/completed/cancelled/missed; routine/urgent |
| encounters | patient_id, appointment_id, facility_code, start_at, end_at, encounter_type | Optional appointment; ordered UTC start/end; outpatient/walk_in |

Common fields: `id` (bounded identifier), `schema_version=1.0.0`, `source_system=synthetic`, `synthetic=true`, positive integer `source_version`, UTC `source_updated_at`, boolean `is_deleted`. All listed fields are required; only appointment_id can be null. Unknown fields are rejected. Tombstones retain the full record shape.

Generator defaults: seed 42, as-of 2026-01-01 UTC, 1,000 patients and 5,000 appointments, of which 4,000 have encounters. Fixed status cycling yields 80% completed, 10% cancelled, 10% missed; these are demonstration rules, not claims about healthcare populations. Completed baseline encounters fall in the 30 days preceding the as-of date. Correction fixtures move an encounter and appointment to a different historical date.

Daily appointment grain: calendar date and facility. Measures: appointments, completed, cancelled, missed, eligible, no_show_rate. Daily encounter grain: start calendar date and facility; measures: encounters and summed integer duration_seconds. Patient summary grain: patient_id; measures: separately aggregated appointments and encounters. UTC is used throughout.
