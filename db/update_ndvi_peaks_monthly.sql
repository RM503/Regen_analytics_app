CREATE OR REPLACE FUNCTION update_ndvi_peaks_monthly()
RETURNS TRIGGER AS $$
BEGIN
	-- Aggregate affected months/regions
	WITH agg AS (
		SELECT
			region,
			TO_CHAR(ndvi_peak_date, 'Mon'),
			EXTRACT(YEAR FROM ndvi_peak_date)::INT AS ndvi_peak_year,
			COUNT(uuid) AS ndvi_peaks_per_month
		FROM ndvipeaksperfarm
		WHERE region IN (
			SELECT DISTINCT region FROM insert_or_deleted
		)
		GROUP BY
			region, 
            TO_CHAR(ndvi_peak_date, 'Mon'), 
            EXTRACT(MONTH FROM ndvi_peak_date),
            EXTRACT(YEAR FROM ndvi_peak_date)
	)
	INSERT INTO ndvipeaksmonthly(region, ndvi_peak_month, ndvi_peak_year, ndvi_peaks_per_month)
    SELECT region, ndvi_peak_month, ndvi_peak_year, ndvi_peaks_per_month
    FROM agg
    ON CONFLICT (region, ndvi_peak_month, ndvi_peak_year)
    DO UPDATE
      SET ndvi_peaks_per_month = EXCLUDED.ndvi_peaks_per_month;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;