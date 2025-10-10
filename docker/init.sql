-- Initialize database for OCR service
-- Note: Database is created by POSTGRES_DB environment variable

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(64) NOT NULL UNIQUE,
    password_hash TEXT        NOT NULL,
    full_name     VARCHAR(128),
    phone         VARCHAR(32) UNIQUE,
    disabled      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users (phone);

-- TODO: Replace the following sample user with secure credentials
INSERT INTO users (username, password_hash, full_name)
VALUES ('sys_lzm', '9e2d54df5cf51936bf8e76ee023373a4', '系统管理员')
ON CONFLICT (username) DO NOTHING;
