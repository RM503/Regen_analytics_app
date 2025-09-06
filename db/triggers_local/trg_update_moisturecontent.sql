DROP TRIGGER IF EXISTS ON trg_update_moisturecontent ON peakvidistribution;

CREATE TRIGGER trg_update_moisturecontent 
AFTER INSERT ON peakvidistribution 
FOR EACH ROW 
EXECUTE FUNCTION update_moisturecontent();