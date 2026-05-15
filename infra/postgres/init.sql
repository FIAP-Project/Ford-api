-- Created on cluster init; idempotent so Alembic can extend further.
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS vehicle;
CREATE SCHEMA IF NOT EXISTS audit;
