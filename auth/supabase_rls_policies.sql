/* Supabase read and write policies */

CREATE POLICY "Read project data"
    ON profiles FOR SELECT
    TO authenticated, anon
    USING (TRUE);

CREATE POLICY "Write project data"
    ON profiles FOR INSERT, UPDATE
    TO authenticated
    WITH CHECK (user_id = auth.uid());