# Milestones

## v1.0 MVP (Shipped: 2026-02-24)

**Phases completed:** 8 phases, 18 plans
**Timeline:** 2 days (Feb 23–24, 2026)
**LOC:** ~3,672 Python + ~213 HTML | 115 tests
**Git range:** e56ced3..b4e59ae

**Delivered:** A lightweight Docker-based search automation daemon for Radarr and Sonarr with a dark theme web UI, round-robin scheduling, and zero credential exposure.

**Key accomplishments:**
- Config, state, and API clients with Pydantic models, SecretStr API keys, loguru redaction, and atomic JSON state
- Round-robin search engine with per-app cursors, season-level Sonarr search, and APScheduler integration
- Dark theme web UI with htmx polling dashboard, config editor, and search-now trigger
- Multi-stage Docker packaging with PUID/PGID privilege dropping, HEALTHCHECK, and localhost detection
- Security hardening — CSRF middleware, SSRF validation, input clamping, Docker least-privilege, vendored htmx
- Comprehensive resilience and test coverage — 115 tests, state recovery, schema migration, race condition fix

---

