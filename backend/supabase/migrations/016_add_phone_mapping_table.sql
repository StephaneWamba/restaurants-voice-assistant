-- Phone number to restaurant_id mapping table
-- Used for routing calls to correct restaurant when using shared assistant
CREATE TABLE IF NOT EXISTS restaurant_phone_mappings (
    phone_number TEXT PRIMARY KEY,
    restaurant_id UUID NOT NULL REFERENCES restaurants (id) ON DELETE CASCADE,
    created_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW (),
        updated_at TIMESTAMP
    WITH
        TIME ZONE DEFAULT NOW ()
);

CREATE INDEX IF NOT EXISTS idx_phone_mappings_restaurant ON restaurant_phone_mappings (restaurant_id);

-- Auto-update trigger
CREATE TRIGGER update_phone_mappings_updated_at BEFORE
UPDATE ON restaurant_phone_mappings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column ();

-- RLS policies
ALTER TABLE restaurant_phone_mappings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role has full access to restaurant_phone_mappings" ON restaurant_phone_mappings FOR ALL TO service_role USING (true)
WITH
    CHECK (true);

CREATE POLICY "Public read access to restaurant_phone_mappings" ON restaurant_phone_mappings FOR
SELECT
    TO anon,
    authenticated USING (true);