CREATE OR REPLACE FUNCTION public.update_ndvi_peaks_monthly()
RETURNS TRIGGER AS $$
DECLARE
    affected_region TEXT;
BEGIN
    -- Determine affected region from inserted/updated/deleted row
    IF (TG_OP = 'DELETE') THEN
        affected_region := OLD.region;
    ELSE
        affected_region := NEW.region;
    END IF;

    -- Aggregate monthly peaks for the affected region
    WITH agg AS (
        SELECT
            region,
            TO_CHAR(ndvi_peak_date, 'Mon') AS ndvi_peak_month,
            EXTRACT(YEAR FROM ndvi_peak_date)::INT AS ndvi_peak_year,
            COUNT(uuid) AS ndvi_peaks_per_month
        FROM public.ndvipeaksperfarm
        WHERE region = affected_region
        GROUP BY region,
                 TO_CHAR(ndvi_peak_date, 'Mon'),
                 EXTRACT(MONTH FROM ndvi_peak_date),
                 EXTRACT(YEAR FROM ndvi_peak_date)
    )
    -- Upsert results into the monthly summary table
    INSERT INTO public.ndvipeaksmonthly(region, ndvi_peak_month, ndvi_peak_year, ndvi_peaks_per_month, updated_at)
    SELECT 
        region, 
        ndvi_peak_month, 
        ndvi_peak_year, 
        ndvi_peaks_per_month,
        now() AS updated_at
    FROM agg
    ON CONFLICT (region, ndvi_peak_month, ndvi_peak_year)
    DO UPDATE SET ndvi_peaks_per_month = EXCLUDED.ndvi_peaks_per_month;

    -- Remove rows in summary table that no longer exist in the source
    DELETE FROM public.ndvipeaksmonthly s
    WHERE s.region = affected_region
      AND NOT EXISTS (
          SELECT 1
          FROM public.ndvipeaksperfarm f
          WHERE f.region = s.region
            AND TO_CHAR(f.ndvi_peak_date, 'Mon') = s.ndvi_peak_month
            AND EXTRACT(YEAR FROM f.ndvi_peak_date)::INT = s.ndvi_peak_year
      );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;
