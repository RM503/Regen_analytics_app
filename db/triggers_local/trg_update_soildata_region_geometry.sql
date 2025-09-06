CREATE TRIGGER trg_update_soildata_region_geometry 
AFTER INSERT ON soildata
FOR EACH ROW 
EXECUTE FUNCTION update_soildata_region_geometry();