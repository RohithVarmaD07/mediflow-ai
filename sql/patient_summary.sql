WITH a AS (SELECT patient_id,count(*) n FROM appointments GROUP BY 1),
e AS (SELECT patient_id,count(*) n FROM encounters GROUP BY 1)
SELECT p.id patient_id, coalesce(a.n,0) appointments, coalesce(e.n,0) encounters
FROM patients p LEFT JOIN a ON p.id=a.patient_id LEFT JOIN e ON p.id=e.patient_id ORDER BY 1;
