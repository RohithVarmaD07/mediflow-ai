CREATE TABLE IF NOT EXISTS records (
    entity VARCHAR NOT NULL,
    id VARCHAR NOT NULL,
    version BIGINT NOT NULL,
    payload VARCHAR NOT NULL,
    PRIMARY KEY (entity, id)
);
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR PRIMARY KEY,
    status VARCHAR NOT NULL,
    evidence VARCHAR NOT NULL
);
CREATE OR REPLACE VIEW patients AS
SELECT id, json_extract_string(payload,'$.birth_date')::DATE birth_date,
json_extract_string(payload,'$.region') region,
json_extract_string(payload,'$.active')::BOOLEAN active
FROM records WHERE entity='patients' AND NOT json_extract_string(payload,'$.is_deleted')::BOOLEAN;
CREATE OR REPLACE VIEW appointments AS
SELECT id, json_extract_string(payload,'$.patient_id') patient_id,
json_extract_string(payload,'$.facility_code') facility_code,
json_extract_string(payload,'$.scheduled_at')::TIMESTAMPTZ scheduled_at,
json_extract_string(payload,'$.status') status
FROM records WHERE entity='appointments' AND NOT json_extract_string(payload,'$.is_deleted')::BOOLEAN;
CREATE OR REPLACE VIEW encounters AS
SELECT id, json_extract_string(payload,'$.patient_id') patient_id,
json_extract_string(payload,'$.appointment_id') appointment_id,
json_extract_string(payload,'$.facility_code') facility_code,
json_extract_string(payload,'$.start_at')::TIMESTAMPTZ start_at,
json_extract_string(payload,'$.end_at')::TIMESTAMPTZ end_at
FROM records WHERE entity='encounters' AND NOT json_extract_string(payload,'$.is_deleted')::BOOLEAN;
SET TimeZone='UTC';
