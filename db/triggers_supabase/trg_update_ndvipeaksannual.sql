DROP TRIGGER IF EXISTS trg_update_ndvi_peaks_annual ON public.ndvipeaksperfarm;

CREATE TRIGGER trg_update_ndvi_peaks_annual
AFTER INSERT OR UPDATE OR DELETE ON public.ndvipeaksperfarm
FOR EACH ROW
EXECUTE FUNCTION public.update_ndvi_peaks_annual();
