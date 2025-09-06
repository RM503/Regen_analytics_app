CREATE OR REPLACE FUNCTION public.update_soildata_region_geometry()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Fully qualify the table name
        SELECT f.region, f.geometry
        INTO NEW.region, NEW.geometry
        FROM public.farmpolygons f
        WHERE f.uuid = NEW.uuid;

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;