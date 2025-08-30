CREATE OR REPLACE FUNCTION update_ndvi_peaks_annual()
RETURNS TRIGGER AS $$
DECLARE
    affected_region TEXT;
    affected_year INT;
BEGIN
    -- Determine affected region/year from inserted/updated/deleted row
    IF (TG_OP = 'DELETE') THEN
        affected_region := OLD.region;
        affected_year   := EXTRACT(YEAR FROM OLD.ndvi_peak_date);
    ELSE
        affected_region := NEW.region;
        affected_year   := EXTRACT(YEAR FROM NEW.ndvi_peak_date);
    END IF;

    -- Recalculate for the affected region-year
    WITH agg AS (
        SELECT
            region,
            EXTRACT(YEAR FROM ndvi_peak_date)::INT AS ndvi_peak_year,
            COUNT(*) AS number_of_peaks_per_farm
        FROM ndvipeaksperfarm
        WHERE region = affected_region
          AND EXTRACT(YEAR FROM ndvi_peak_date) = affected_year
        GROUP BY uuid, region, EXTRACT(YEAR FROM ndvi_peak_date)
    ),
    final_agg AS (
        SELECT
            ndvi_peak_year,
            region,
            number_of_peaks_per_farm,
            COUNT(*) AS uuid_count
        FROM agg
        GROUP BY ndvi_peak_year, region, number_of_peaks_per_farm
    )
    -- Upsert results into summary table
    INSERT INTO ndvipeaksperfarm_summary (region, ndvi_peak_year, number_of_peaks_per_farm, uuid_count)
    SELECT region, ndvi_peak_year, number_of_peaks_per_farm, uuid_count
    FROM final_agg
    ON CONFLICT (region, ndvi_peak_year, number_of_peaks_per_farm)
    DO UPDATE
      SET uuid_count = EXCLUDED.uuid_count;

    -- Remove any rows for this region/year no longer present
    DELETE FROM ndvipeaksperfarm_summary s
    WHERE s.region = affected_region
      AND s.ndvi_peak_year = affected_year
      AND NOT EXISTS (
          SELECT 1 FROM final_agg f
          WHERE f.region = s.region
            AND f.ndvi_peak_year = s.ndvi_peak_year
            AND f.number_of_peaks_per_farm = s.number_of_peaks_per_farm
      );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;