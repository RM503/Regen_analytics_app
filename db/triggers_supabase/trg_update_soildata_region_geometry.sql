DROP TRIGGER IF EXISTS trg_update_soildata_region_geometry ON public.soildata;

CREATE TRIGGER trg_update_soildata_region_geometry
BEFORE INSERT OR UPDATE OR DELETE ON public.soildata
FOR EACH ROW
EXECUTE FUNCTION public.update_soildata_region_geometry();