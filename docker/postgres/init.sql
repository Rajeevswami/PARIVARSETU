-- Extensions ParivarSetu relies on: uuid-ossp for UUID primary keys,
-- pg_trgm for fast fuzzy/partial-text search on names and descriptions.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
