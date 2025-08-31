CREATE OR REPLACE FUNCTION update_soildata_region_geometry()
RETURNS TRIGGER AS $$
BEGIN
	/* Updates soildata table with region and geometry from farmpolygons */
	UPDATE soildata s
	SET region = f.region,
		geometry = f.geometry
	FROM farmpolygons f
	WHERE s.uuid = f.uuid AND s.uuid = NEW.uuid;
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;