-- Fix RLS policies for service_role access
-- Run this in Supabase SQL Editor if seeding fails with RLS errors

-- Drop and recreate policies for service_role
DROP POLICY IF EXISTS "Service role has full access to restaurants" ON restaurants;
DROP POLICY IF EXISTS "Service role has full access to menu_items" ON menu_items;
DROP POLICY IF EXISTS "Service role has full access to modifiers" ON modifiers;
DROP POLICY IF EXISTS "Service role has full access to operating_hours" ON operating_hours;
DROP POLICY IF EXISTS "Service role has full access to delivery_zones" ON delivery_zones;
DROP POLICY IF EXISTS "Service role has full access to document_embeddings" ON document_embeddings;
DROP POLICY IF EXISTS "Service role has full access to call_history" ON call_history;

-- Create policies for service_role
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

