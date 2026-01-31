-- KAVACH-INFINITY Database Initialization
-- This script runs when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create enum types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('super_admin', 'admin', 'operator', 'analyst', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE sensor_type AS ENUM ('temperature', 'humidity', 'pressure', 'vibration', 'power', 
                                      'radar', 'thermal', 'gas', 'motion', 'proximity', 'network', 'custom');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE sensor_status AS ENUM ('online', 'offline', 'degraded', 'maintenance', 'fault');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_severity AS ENUM ('critical', 'high', 'medium', 'low', 'info');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM ('active', 'acknowledged', 'resolved', 'suppressed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE domain_type AS ENUM ('railway', 'metro', 'power', 'industrial', 'smartcity', 'it_ot', 'custom');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create default admin user (password: Admin@123)
-- Password hash generated with bcrypt
INSERT INTO users (id, username, email, password_hash, full_name, role, is_active, created_at)
VALUES (
    uuid_generate_v4(),
    'admin',
    'admin@kavach.io',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4tGxKJOYhL8XvvDq',
    'System Administrator',
    'super_admin',
    true,
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Create sample site
INSERT INTO sites (id, name, code, domain, location, is_active, created_at)
VALUES (
    uuid_generate_v4(),
    'Demo Railway Junction',
    'RLY-001',
    'railway',
    '{"lat": 28.6139, "lng": 77.2090, "address": "Delhi, India"}',
    true,
    NOW()
) ON CONFLICT (code) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_site_id ON alerts(site_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_triggered_at ON alerts(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_sensors_site_id ON sensors(site_id);
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kavach;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kavach;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'KAVACH-INFINITY database initialized successfully';
END $$;
