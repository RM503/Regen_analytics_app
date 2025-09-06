CREATE OR REPLACE FUNCTION public.update_moisturecontent()
RETURNS TRIGGER AS $$
DECLARE
    affected_region TEXT;
BEGIN
    -- Handle INSERT/UPDATE/DELETE consistently
    IF TG_OP = 'DELETE' THEN
        affected_region := OLD.region;
    ELSE
        affected_region := NEW.region;
    END IF;

    -- Clear existing aggregates for that region
    DELETE FROM public.moisturecontent
    WHERE region = affected_region;

    -- Recompute and insert updated aggregates
    INSERT INTO public.moisturecontent (region, moisture_content, counts, updated_at)
    SELECT
        region,
        moisture_content,
        COUNT(*) AS counts,
        now() AS updated_at
    FROM (
        SELECT
            uuid,
            region,
            CASE
                WHEN AVG(ndmi_max) OVER (PARTITION BY uuid, region) >= 0.38 THEN 'high'
                WHEN AVG(ndmi_max) OVER (PARTITION BY uuid, region) >= 0.25
                     AND AVG(ndmi_max) OVER (PARTITION BY uuid, region) < 0.38 THEN 'medium'
                WHEN AVG(ndmi_max) OVER (PARTITION BY uuid, region) >= 0.20
                     AND AVG(ndmi_max) OVER (PARTITION BY uuid, region) < 0.25 THEN 'approaching low'
                ELSE 'low'
            END AS moisture_content
        FROM public.peakvidistribution
        WHERE region = affected_region
    ) categorized
    GROUP BY region, moisture_content;

    -- AFTER trigger, so return NULL
    RETURN NULL;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;
