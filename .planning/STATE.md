# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** Reliably trigger searches in Radarr and Sonarr for missing and upgrade-eligible media on a schedule, without exposing credentials or expanding attack surface.
**Current focus:** Phase 3 — Web UI

## Current Position

Phase: 3 of 4 (Web UI)
Plan: 1 of 3 in current phase
Status: In Progress
Last activity: 2026-02-23 — Completed 03-01-PLAN.md (Web UI infrastructure)

Progress: [███████████████████████░░░░░] 70%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 2min
- Total execution time: 17min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 3/3 | 8min | 3min |
| 2. Search Engine | 3/3 | 6min | 2min |
| 3. Web UI | 1/3 | 3min | 3min |

**Recent Trend:**
- Last 5 plans: 01-03 (2min), 02-01 (2min), 02-02 (2min), 02-03 (2min), 03-01 (3min)
- Trend: Consistent

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Python/FastAPI + htmx/Jinja2 stack chosen for familiarity and minimal build surface
- [Init]: Season-level Sonarr search (SeasonSearch) confirmed — avoids indexer hammering
- [Init]: JSON file with atomic write chosen for state store (simpler than SQLite for cursor + bounded log)
- [Init]: API keys in X-Api-Key header only — never query params, never in any response body
- [01-01]: Settings loads via init_settings + TomlConfigSettingsSource for testability with arbitrary TOML paths
- [01-01]: Config loader reads TOML via tomllib and passes parsed data as init kwargs for path flexibility
- [01-01]: Default config uses plain text template to preserve inline comments
- [01-02]: Content-Type: application/json set on all requests for Sonarr v4 compatibility
- [01-02]: validate_connection calls system/status directly (no retry) for clear startup diagnostics
- [01-02]: Pagination terminates on zero records OR page*pageSize >= totalRecords
- [01-03]: Startup accepts optional config_path parameter for testability
- [01-03]: Clients created and closed during validation -- search engine creates its own in Phase 2
- [01-03]: pytest-asyncio asyncio_mode=auto for seamless async test support
- [02-01]: Search fields use simple attribute defaults matching existing ArrConfig pattern
- [02-01]: Default config comments out search fields since defaults (30 min, 5, 5) are sensible
- [02-02]: Top-level abort catches httpx.HTTPError and subclasses for all network/HTTP failure modes
- [02-02]: Per-item search failures catch broad Exception for maximum skip-and-continue resilience
- [02-03]: APScheduler 3.x chosen over 4.x (4.x still alpha, 3.x stable with AsyncIOScheduler)
- [02-03]: Uvicorn log_level=warning to keep loguru as sole log channel
- [02-03]: State shared by reference via nonlocal in job closures (safe: same event loop)
- [03-01]: Tailwind CSS v4 compiled via pytailwindcss (v4.2.1 binary auto-downloaded)
- [03-01]: Job closures read from app.state at execution time for hot-reload readiness
- [03-01]: Active nav link uses Jinja2 block overrides instead of URL comparison

### Pending Todos

None yet.

### Blockers/Concerns

- Sonarr v3 vs v4 API: startup version check should log version; always set Content-Type: application/json on POST requests to handle v4 strict enforcement
- pageSize ceiling: log total item count fetched each cycle so users can diagnose unexpected truncation on large libraries

## Session Continuity

Last session: 2026-02-23
Stopped at: Completed 03-01-PLAN.md
Resume file: None
