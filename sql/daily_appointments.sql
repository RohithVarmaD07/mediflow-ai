SELECT scheduled_at::DATE AS day, facility_code, count(*) appointments,
count(*) FILTER (WHERE status='completed') completed,
count(*) FILTER (WHERE status='cancelled') cancelled,
count(*) FILTER (WHERE status='missed') missed,
count(*) FILTER (WHERE status IN ('completed','missed')) eligible,
count(*) FILTER (WHERE status='missed')::DOUBLE /
nullif(count(*) FILTER (WHERE status IN ('completed','missed')),0) no_show_rate
FROM appointments GROUP BY 1,2 ORDER BY 1,2;
