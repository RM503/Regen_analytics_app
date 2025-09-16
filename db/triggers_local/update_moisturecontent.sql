CREATE OR REPLACE FUNCTION update_moisturecontent()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM moisturecontent
    WHERE region = NEW.region;

    INSERT INTO moisturecontent (region, moisture_content, counts)
    SELECT
        region,
        moisture_content,
        COUNT(DISTINCT uuid) AS counts
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
        FROM peakvidistribution
        WHERE region = NEW.region
    ) categorized
    GROUP BY region, moisture_content;

    RETURN NEW;
END
$$ LANGUAGE plpgsql;
