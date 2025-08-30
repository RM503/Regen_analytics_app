/* ndvipeaksannual */
SELECT
    ndvi_peak_year,
    region,
    number_of_peaks_per_farm,
    COUNT(*) AS uuid_count
FROM (
    -- Step 1: count peaks per farm per year
    SELECT
        uuid,
        region,
        EXTRACT(YEAR FROM ndvi_peak_date) AS ndvi_peak_year,
        COUNT(*) AS number_of_peaks_per_farm
    FROM ndvipeaksperfarm
    GROUP BY uuid, region, EXTRACT(YEAR FROM ndvi_peak_date)
) sub
-- Step 2: count how many farms had each peak multiplicity
GROUP BY ndvi_peak_year, region, number_of_peaks_per_farm
ORDER BY ndvi_peak_year, region, number_of_peaks_per_farm
LIMIT 100;