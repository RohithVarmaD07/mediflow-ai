SELECT 'patients' entity, count(*) active_rows FROM patients
UNION ALL SELECT 'appointments',count(*) FROM appointments
UNION ALL SELECT 'encounters',count(*) FROM encounters;
