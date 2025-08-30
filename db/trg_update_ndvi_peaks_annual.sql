DROP TRIGGER IF EXISTS trg_update_ndvi_peaks_annual ON ndvipeaksperfarm;

CREATE TRIGGER trg_update_ndvi_peaks_annual 
AFTER INSERT OR UPDATE OR DELETE 
ON ndvipeaksperfarm 
FOR EACH ROW
EXECUTE FUNCTION update_ndvi_peaks_annual();