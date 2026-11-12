-- scdchain initial schema (PostgreSQL 16) — mirror of src/models/*
-- Runtime bootstraps the same DDL via SQLAlchemy create_all().
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    display_name VARCHAR(64) NOT NULL,
    role VARCHAR(16) NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_systems (
    id SERIAL PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(64) NOT NULL,
    system_type VARCHAR(32) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    contact_owner VARCHAR(64) NOT NULL DEFAULT '',
    snapshot_time VARCHAR(16) NOT NULL DEFAULT '02:00',
    trust_level INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_snapshots (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES source_systems(id),
    source_code VARCHAR(32) NOT NULL,
    business_key VARCHAR(32) NOT NULL,
    snapshot_date DATE NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    row_hash VARCHAR(64) NOT NULL,
    ingested_at TIMESTAMP NOT NULL,
    is_late BOOLEAN NOT NULL DEFAULT FALSE,
    batch_tag VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_snapshot_natural UNIQUE (source_id, business_key, snapshot_date)
);
CREATE INDEX IF NOT EXISTS ix_snapshot_key_date ON customer_snapshots (business_key, snapshot_date);

CREATE TABLE IF NOT EXISTS merge_rules (
    id SERIAL PRIMARY KEY,
    attribute_key VARCHAR(48) NOT NULL UNIQUE,
    display_name VARCHAR(48) NOT NULL,
    data_type VARCHAR(16) NOT NULL,
    source_priority JSONB NOT NULL DEFAULT '[]'::jsonb,
    normalization VARCHAR(24) NOT NULL DEFAULT 'direct',
    exclude_from_change BOOLEAN NOT NULL DEFAULT FALSE,
    description VARCHAR(255) NOT NULL DEFAULT '',
    updated_by VARCHAR(120) NOT NULL DEFAULT '',
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS build_runs (
    id SERIAL PRIMARY KEY,
    run_no INTEGER NOT NULL,
    label VARCHAR(64) NOT NULL UNIQUE,
    mode VARCHAR(16) NOT NULL DEFAULT 'full',
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    triggered_by VARCHAR(120) NOT NULL DEFAULT 'seed',
    as_of_cutoff DATE,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    invariants JSONB NOT NULL DEFAULT '{}'::jsonb,
    input_hash VARCHAR(64) NOT NULL DEFAULT '',
    previous_run_id INTEGER,
    error_message VARCHAR(512) NOT NULL DEFAULT '',
    notes VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dim_customers (
    id SERIAL PRIMARY KEY,
    build_run_id INTEGER NOT NULL REFERENCES build_runs(id),
    business_key VARCHAR(32) NOT NULL,
    version INTEGER NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    version_source VARCHAR(24) NOT NULL DEFAULT 'merge',
    change_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_dim_run_key_version UNIQUE (build_run_id, business_key, version)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_dim_run_current
    ON dim_customers (build_run_id, business_key) WHERE is_current;
CREATE INDEX IF NOT EXISTS ix_dim_run_asof ON dim_customers (build_run_id, business_key, valid_from);

CREATE TABLE IF NOT EXISTS conflict_items (
    id SERIAL PRIMARY KEY,
    business_key VARCHAR(32) NOT NULL,
    attribute_key VARCHAR(48) NOT NULL,
    snapshot_date DATE NOT NULL,
    candidates JSONB NOT NULL DEFAULT '[]'::jsonb,
    verdict VARCHAR(24) NOT NULL DEFAULT 'conflict',
    similarity DOUBLE PRECISION NOT NULL DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'open',
    resolution JSONB NOT NULL DEFAULT '{}'::jsonb,
    resolved_by VARCHAR(120) NOT NULL DEFAULT '',
    resolved_at TIMESTAMP,
    first_run_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_conflict_key_attr UNIQUE (business_key, attribute_key)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor_email VARCHAR(120) NOT NULL DEFAULT '',
    actor_role VARCHAR(16) NOT NULL DEFAULT '',
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(32) NOT NULL DEFAULT '',
    resource_id VARCHAR(64) NOT NULL DEFAULT '',
    detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip VARCHAR(64) NOT NULL DEFAULT '',
    request_id VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
