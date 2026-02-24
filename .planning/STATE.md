# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** Reliably trigger searches in Radarr and Sonarr for missing and upgrade-eligible media on a schedule, without exposing credentials or expanding attack surface.
**Current focus:** Phase 2 — Search Engine

## Current Position

Phase: 2 of 4 (Search Engine)
Plan: 2 of 3 in current phase
Status: Executing
Last activity: 2026-02-23 — Completed 02-02-PLAN.md (search cycle orchestrators: run_radarr_cycle, run_sonarr_cycle)

Progress: [████████████████░░░░] 50%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 2min
- Total execution time: 12min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 3/3 | 8min | 3min |
| 2. Search Engine | 2/3 | 4min | 2min |

**Recent Trend:**
- Last 5 plans: 01-01 (4min), 01-02 (2min), 01-03 (2min), 02-01 (2min), 02-02 (2min)
- Trend: Accelerating

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

### Pending Todos

None yet.

### Blockers/Concerns

- Sonarr v3 vs v4 API: startup version check should log version; always set Content-Type: application/json on POST requests to handle v4 strict enforcement
- pageSize ceiling: log total item count fetched each cycle so users can diagnose unexpected truncation on large libraries

## Session Continuity

Last session: 2026-02-23
Stopped at: Completed 02-02-PLAN.md
Resume file: None
