-- Drop all tables for complete reset
-- WARNING: This will delete all data!

DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;

-- Drop functions
DROP FUNCTION IF EXISTS search_documents(UUID, TEXT, TEXT, INTEGER, DOUBLE PRECISION);
DROP FUNCTION IF EXISTS update_updated_at_column();

