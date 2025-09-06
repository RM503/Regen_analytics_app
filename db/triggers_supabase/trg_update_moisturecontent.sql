DROP TRIGGER IF EXISTS trg_update_moisturecontent ON public.peakvidistribution;

CREATE TRIGGER trg_update_moisturecontent
AFTER INSERT OR UPDATE OR DELETE ON public.peakvidistribution
FOR EACH ROW
EXECUTE FUNCTION public.update_moisturecontent();
