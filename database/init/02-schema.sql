-- ============================================================
-- LancasterLink – Database Schema
-- Core tables for timetable, stop, route, and live data.
-- Aligns with Data Design (Section 4) of the Design Document.
-- ============================================================

-- ----- NPTG Localities (towns/cities) -----
CREATE TABLE IF NOT EXISTS localities (
    locality_code   VARCHAR(20) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    region          VARCHAR(100),
    geom            GEOMETRY(Point, 4326)
);

-- ----- NaPTAN Stops (bus stops, tram stops, rail stations) -----
CREATE TABLE IF NOT EXISTS stops (
    atco_code       VARCHAR(20) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    locality_code   VARCHAR(20) REFERENCES localities(locality_code),
    stop_type       VARCHAR(20) NOT NULL,       -- 'bus', 'rail', 'tram'
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    geom            GEOMETRY(Point, 4326),
    hub_score       DOUBLE PRECISION DEFAULT 0  -- RL-02: hub prioritisation metric
);

CREATE INDEX IF NOT EXISTS idx_stops_geom ON stops USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_stops_locality ON stops(locality_code);
CREATE INDEX IF NOT EXISTS idx_stops_name_trgm ON stops USING GIN(name gin_trgm_ops);

-- ----- Routes (operator service definitions) -----
CREATE TABLE IF NOT EXISTS routes (
    route_id        SERIAL PRIMARY KEY,
    operator        VARCHAR(100) NOT NULL,
    route_name      VARCHAR(255) NOT NULL,
    transport_mode  VARCHAR(20) NOT NULL,       -- 'bus', 'rail', 'tram'
    route_geom      GEOMETRY(LineString, 4326)  -- Optional: full route geometry
);

-- ----- Timetable entries (scheduled stop times) -----
CREATE TABLE IF NOT EXISTS timetable (
    timetable_id    SERIAL PRIMARY KEY,
    route_id        INTEGER NOT NULL REFERENCES routes(route_id),
    stop_atco_code  VARCHAR(20) NOT NULL REFERENCES stops(atco_code),
    stop_sequence   INTEGER NOT NULL,
    arrival_time    TIME,
    departure_time  TIME,
    days_of_week    VARCHAR(20),                -- e.g. 'MoTuWeThFr', 'SaSu'
    valid_from      DATE,
    valid_to        DATE
);

CREATE INDEX IF NOT EXISTS idx_timetable_route ON timetable(route_id);
CREATE INDEX IF NOT EXISTS idx_timetable_stop ON timetable(stop_atco_code);

-- ----- Live Vehicle Positions -----
CREATE TABLE IF NOT EXISTS live_vehicles (
    vehicle_id      VARCHAR(50) PRIMARY KEY,
    route_id        INTEGER REFERENCES routes(route_id),
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    bearing         DOUBLE PRECISION,
    speed           DOUBLE PRECISION,
    transport_mode  VARCHAR(20) NOT NULL,
    last_updated    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    geom            GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS idx_live_vehicles_geom ON live_vehicles USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_live_vehicles_updated ON live_vehicles(last_updated);

-- ----- Disruptions & Service Alerts -----
CREATE TABLE IF NOT EXISTS disruptions (
    disruption_id   SERIAL PRIMARY KEY,
    route_id        INTEGER REFERENCES routes(route_id),
    stop_atco_code  VARCHAR(20) REFERENCES stops(atco_code),
    disruption_type VARCHAR(30) NOT NULL,       -- 'cancelled', 'delayed', 'diverted'
    description     TEXT,
    severity        VARCHAR(20),                -- 'minor', 'moderate', 'severe'
    start_time      TIMESTAMP WITH TIME ZONE,
    end_time        TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_disruptions_route ON disruptions(route_id);
CREATE INDEX IF NOT EXISTS idx_disruptions_active ON disruptions(start_time, end_time);

-- ----- Walking Connections (between nearby stops/stations) -----
CREATE TABLE IF NOT EXISTS walking_connections (
    from_atco_code  VARCHAR(20) NOT NULL REFERENCES stops(atco_code),
    to_atco_code    VARCHAR(20) NOT NULL REFERENCES stops(atco_code),
    walk_time_mins  DOUBLE PRECISION NOT NULL,
    distance_metres DOUBLE PRECISION,
    PRIMARY KEY (from_atco_code, to_atco_code)
);

-- ----- Saved Journeys (optional: for FR-JP-06 COULD user accounts) -----
CREATE TABLE IF NOT EXISTS saved_journeys (
    journey_id      SERIAL PRIMARY KEY,
    user_hash       VARCHAR(255),               -- Hashed identifier (no PII stored)
    origin_atco     VARCHAR(20) REFERENCES stops(atco_code),
    destination_atco VARCHAR(20) REFERENCES stops(atco_code),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
