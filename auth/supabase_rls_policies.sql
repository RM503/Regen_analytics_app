/* Supabase read and write policies */

-- FarmPolygons
ALTER TABLE farmpolygons ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read farmpolygons"
    ON farmpolygons FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write farmpolygons"
    ON farmpolygons FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);

-- HighNDMIDays
ALTER TABLE highndmidays ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read highndmidays"
    ON highndmidays FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write highndmidays"
    ON highndmidays FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);

-- MoistureContent
ALTER TABLE moisturecontent ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read moisturecontent"
    ON moisturecontent FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write moisturecontent"
    ON moisturecontent FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);

-- NDVIPeaksAnnual
ALTER TABLE ndvipeaksannual ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read ndvipeaksannual"
    ON ndvipeaksannual FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write ndvipeaksannual"
    ON ndvipeaksannual FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);

-- NDVIPeaksMonthly
ALTER TABLE ndvipeaksmonthly ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read ndvipeaksmonthly"
    ON ndvipeaksmonthly FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICTY "Write ndvipeaksmonthly"
    ON ndvipeaksmonthly FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);

-- NDVIPeaksPerFarm
ALTER TABLE ndvipeaksperfarm ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read ndvipeaksperfarm"
    ON ndvipeaksperfarm FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write ndvipeaksperfarm"
    ON ndvipeaksperfarm FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);

-- PeakVidistribution
ALTER TABLE peakvidistribution ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read peakvidistribution"
    ON peakvidistribution FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write peakvidistribution"
    ON peakvidistribution FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);

-- Soildata
ALTER TABLE soildata ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Read soildata"
    ON soildata FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write soildata"
    ON soildata FOR INSERT, UPDATE
    TO authenticated
    USING (TRUE)
    WITH CHECK (TRUE);