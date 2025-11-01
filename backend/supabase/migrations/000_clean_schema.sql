-- CLEAN DATABASE SCHEMA - Only tables and features actually used
-- Run this to create a fresh database with only what's needed
-- 
-- Usage: Drop existing database/schema, then run this migration

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS vector; -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- ============================================================================
-- TABLES
-- ============================================================================

-- Core tenant table
CREATE TABLE IF NOT EXISTS restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Menu items
CREATE TABLE IF NOT EXISTS menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category TEXT DEFAULT 'General',
    available BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Modifiers (old structure - currently used in code)
CREATE TABLE IF NOT EXISTS modifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Operating hours
CREATE TABLE IF NOT EXISTS operating_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    day_of_week TEXT NOT NULL,
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    is_closed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Delivery zones
CREATE TABLE IF NOT EXISTS delivery_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    zone_name TEXT NOT NULL,
    description TEXT,
    delivery_fee DECIMAL(10, 2) NOT NULL,
    min_order DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document embeddings for vector search
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small dimension
    category TEXT NOT NULL CHECK (category IN ('menu', 'modifiers', 'hours', 'zones')),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Call history
CREATE TABLE IF NOT EXISTS call_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    caller TEXT,
    outcome TEXT,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant ON menu_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_modifiers_restaurant ON modifiers(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_operating_hours_restaurant ON operating_hours(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_delivery_zones_restaurant ON delivery_zones(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_document_embeddings_restaurant ON document_embeddings(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_document_embeddings_category ON document_embeddings(category);
CREATE INDEX IF NOT EXISTS idx_document_embeddings_restaurant_category ON document_embeddings(restaurant_id, category);
CREATE INDEX IF NOT EXISTS idx_call_history_restaurant ON call_history(restaurant_id);

-- Vector index for similarity search (HNSW for better performance)
CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector ON document_embeddings 
USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Vector similarity search function
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(1536),
    query_restaurant_id uuid,
    query_category text DEFAULT NULL,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    category text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_embeddings.id,
        document_embeddings.content,
        document_embeddings.metadata,
        document_embeddings.category,
        1 - (document_embeddings.embedding <=> query_embedding) as similarity
    FROM document_embeddings
    WHERE 
        document_embeddings.restaurant_id = query_restaurant_id
        AND (query_category IS NULL OR document_embeddings.category = query_category)
        AND document_embeddings.embedding IS NOT NULL
    ORDER BY document_embeddings.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION search_documents TO service_role;
GRANT EXECUTE ON FUNCTION search_documents TO anon;
GRANT EXECUTE ON FUNCTION search_documents TO authenticated;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update triggers
CREATE TRIGGER update_restaurants_updated_at BEFORE UPDATE ON restaurants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_menu_items_updated_at BEFORE UPDATE ON menu_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_modifiers_updated_at BEFORE UPDATE ON modifiers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_operating_hours_updated_at BEFORE UPDATE ON operating_hours
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_delivery_zones_updated_at BEFORE UPDATE ON delivery_zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_embeddings_updated_at BEFORE UPDATE ON document_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE restaurants ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE modifiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE operating_hours ENABLE ROW LEVEL SECURITY;
ALTER TABLE delivery_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_history ENABLE ROW LEVEL SECURITY;

-- Service role has full access to all tables
CREATE POLICY "Service role has full access to restaurants"
ON restaurants FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to menu_items"
ON menu_items FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to modifiers"
ON modifiers FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to operating_hours"
ON operating_hours FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to delivery_zones"
ON delivery_zones FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to document_embeddings"
ON document_embeddings FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role has full access to call_history"
ON call_history FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Public read access (for frontend if needed)
CREATE POLICY "Public read access to restaurants"
ON restaurants FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public read access to menu_items"
ON menu_items FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public read access to modifiers"
ON modifiers FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public read access to operating_hours"
ON operating_hours FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public read access to delivery_zones"
ON delivery_zones FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public read access to document_embeddings"
ON document_embeddings FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Public read access to call_history"
ON call_history FOR SELECT TO anon, authenticated USING (true);
