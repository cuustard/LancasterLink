-- ============================================================
-- LancasterLink – Database Initialisation: Extensions
-- Runs automatically on first container start via
-- /docker-entrypoint-initdb.d/
-- ============================================================

-- Enable PostGIS for geospatial queries (stop proximity, walking legs)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pg_trgm for fuzzy text search on stop/locality names
CREATE EXTENSION IF NOT EXISTS pg_trgm;
