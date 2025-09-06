CREATE OR REPLACE FUNCTION public.update_ndvi_peaks_annual()
RETURNS TRIGGER AS $$
DECLARE
    affected_region TEXT;
    affected_year   INT;
BEGIN
    -- Determine affected row(s)
    IF (TG_OP = 'DELETE') THEN
        affected_region := OLD.region;
        affected_year   := EXTRACT(YEAR FROM OLD.ndvi_peak_date)::INT;
    ELSE
        affected_region := NEW.region;
        affected_year   := EXTRACT(YEAR FROM NEW.ndvi_peak_date)::INT;
    END IF;

    -- Step 1: count peaks per farm per year
    WITH peaks_per_farm AS (
        SELECT
            uuid,
            region,
            EXTRACT(YEAR FROM ndvi_peak_date)::INT AS ndvi_peak_year,
            COUNT(*) AS number_of_peaks_per_farm
        FROM public.ndvipeaksperfarm
        WHERE region = affected_region
          AND EXTRACT(YEAR FROM ndvi_peak_date)::INT = affected_year
        GROUP BY uuid, region, EXTRACT(YEAR FROM ndvi_peak_date)
    ),
    -- Step 2: count how many farms had each peak multiplicity
    farm_counts AS (
        SELECT
            ndvi_peak_year,
            region,
            number_of_peaks_per_farm,
            COUNT(*) AS uuid_count
        FROM peaks_per_farm
        GROUP BY ndvi_peak_year, region, number_of_peaks_per_farm
    )
    -- Upsert into summary table
    INSERT INTO public.ndvipeaksannual (
        ndvi_peak_year, 
        region, 
        number_of_peaks_per_farm, 
        uuid_count,
        updated_at
    )
    SELECT 
        ndvi_peak_year, 
        region, 
        number_of_peaks_per_farm, 
        uuid_count,
        now() AS updated_at
    FROM farm_counts
    ON CONFLICT (ndvi_peak_year, region, number_of_peaks_per_farm)
    DO UPDATE
      SET 
        uuid_count = EXCLUDED.uuid_count,
        updated_at = now();

    RETURN NULL;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;
