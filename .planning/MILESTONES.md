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


## v1.1 Ship & Document (Shipped: 2026-02-24)

**Phases completed:** 4 phases, 5 plans
**Timeline:** 2026-02-24 (same day as v1.0)
**Git range:** v1.0..HEAD (30 commits)
**Files:** 49 files changed, +4,192 -173 lines

**Delivered:** CI/CD pipeline, automated Docker releases to GHCR, search enhancements (hard max cap + SQLite history), and comprehensive README documentation.

**Key accomplishments:**
- GitHub Actions CI with pytest, ruff linting, and Docker build validation in three parallel jobs
- Automated GHCR publishing — `:dev` on push to main, `:latest` + version tag on release
- Hard max items per cycle with proportional batch capping and settings UI integration
- SQLite persistent search history with auto-migration from JSON and 500-row auto-pruning
- Complete README with Docker install guide, TOML config reference, security model, and screenshot placeholders

---

