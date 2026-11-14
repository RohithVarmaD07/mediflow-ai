SELECT start_at::DATE AS day, facility_code, count(*) encounters,
sum(date_diff('second',start_at,end_at)) duration_seconds
FROM encounters GROUP BY 1,2 ORDER BY 1,2;
