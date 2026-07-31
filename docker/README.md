# docker/

Shared infrastructure-level Docker assets that aren't specific to a single
service.

- `postgres/init.sql` — extensions (uuid-ossp, pg_trgm) enabled on first
  container start, required by our UUID primary keys and search features.

Service Dockerfiles live next to the code they build: `backend/Dockerfile`,
`frontend/Dockerfile`, `nginx/Dockerfile` (reverse proxy, prod only).
