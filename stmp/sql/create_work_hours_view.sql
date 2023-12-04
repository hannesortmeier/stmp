CREATE VIEW {} AS
SELECT
    date,
    start_time,
    end_time,
    break_minutes,
    work_hours,
    ROUND(work_hours - {}, 2) AS overtime_hours,
    SUM(ROUND(work_hours - {}, 2)) OVER(ORDER BY row_num ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_overtime_hours
FROM (SELECT
        date,
        start_time,
        end_time,
        break_minutes,
        ROUND(((CAST(strftime('%H', end_time) AS REAL) - CAST(strftime('%H', start_time) AS REAL)) * 60
        + (CAST(strftime('%M', end_time) AS REAL) - CAST(strftime('%M', start_time) AS REAL)) - break_minutes) / 60, 2) AS work_hours,
        ROW_NUMBER() OVER(ORDER BY date) AS row_num
    FROM work_hours);