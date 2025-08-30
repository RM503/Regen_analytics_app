/* ndvipeaksmonthly */
SELECT region, ndvi_peak_month, ndvi_peak_year, ndvi_peaks_per_month
FROM (
  SELECT 
    region,
    TO_CHAR(ndvi_peak_date, 'Mon') AS ndvi_peak_month,
    EXTRACT(MONTH FROM ndvi_peak_date) AS month_num,
    EXTRACT(YEAR FROM ndvi_peak_date) AS ndvi_peak_year,
    COUNT(uuid) AS ndvi_peaks_per_month
  FROM ndvipeaksperfarm
  GROUP BY 
    region, 
    TO_CHAR(ndvi_peak_date, 'Mon'), 
    EXTRACT(MONTH FROM ndvi_peak_date),
    EXTRACT(YEAR FROM ndvi_peak_date)
) sub 
ORDER BY region, ndvi_peak_year, month_num;