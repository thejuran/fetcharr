# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** Reliably trigger searches in Radarr and Sonarr for missing and upgrade-eligible media on a schedule, without exposing credentials or expanding attack surface.
**Current focus:** Phase 6 — Bug Fixes & Resilience (In Progress)

## Current Position

Phase: 6 of 7 (Bug Fixes & Resilience)
Plan: 3 of 3 in current phase (COMPLETE)
Status: Phase Complete
Last activity: 2026-02-24 — Completed 06-03 (Concurrency lock, settings validation, traceback redaction)

Progress: [█████████████████████████░░░░░] 86% (6/7 phases)

## Performance Metrics

**Velocity:**
- Total plans completed: 15
- Average duration: 2min
- Total execution time: 34min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 3/3 | 8min | 3min |
| 2. Search Engine | 3/3 | 6min | 2min |
| 3. Web UI | 3/3 | 8min | 3min |
| 4. Docker | 1/1 | 2min | 2min |
| 5. Security Hardening | 2/2 | 4min | 2min |
| 6. Bug Fixes & Resilience | 3/3 | 6min | 2min |

**Recent Trend:**
- Last 5 plans: 05-01 (2min), 05-02 (2min), 06-01 (2min), 06-02 (2min), 06-03 (2min)
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
- [03-02]: Raw item counts cached before filtering so dashboard shows total wanted/cutoff items
- [03-02]: Connection health uses first-failure timestamp for unreachable_since (not updated on subsequent failures)
- [03-02]: App badges use Radarr orange and Sonarr blue ecosystem branding in search log
- [03-03]: API key masking uses password field with empty value + conditional placeholder (never real key in HTML)
- [03-03]: python-multipart added as runtime dependency for FastAPI form parsing
- [03-03]: Client recreation on URL/key change to avoid stale connections after config edit
- [04-01]: pytailwindcss in builder stage only -- not installed in production image
- [04-01]: HEALTHCHECK uses python3 urllib.request instead of curl (no extra binary in slim image)
- [04-01]: entrypoint.sh uses exec setpriv so python becomes PID 1 and receives SIGTERM directly
- [04-01]: docker-compose.yml references ghcr.io image with comment about local build alternative
- [05-01]: Origin/Referer header check over CSRF tokens -- no auth/sessions means no cookies to protect
- [05-01]: cap_drop ALL + cap_add CHOWN/SETUID/SETGID to keep entrypoint working while minimizing capabilities
- [05-01]: Vendored htmx.min.js committed to repo (not build-time download) for reproducible builds
- [05-02]: Empty URL is valid (app disabled state) -- not rejected by validation
- [05-02]: Private-network IPs (10.x, 192.168.x) intentionally allowed since *arr apps run on LAN
- [05-02]: Invalid URL redirects back to /settings with no flash message (acceptable for security hardening pass)
- [06-01]: Shallow merge per app key preserves loaded values while filling missing keys from defaults
- [06-01]: Type-checked merge: only merge dicts for app keys, only replace search_log with lists
- [06-02]: TransportError replaces ConnectError+TimeoutException in retry catch (covers RemoteProtocolError, ReadError)
- [06-02]: httpx.HTTPError replaces redundant subcatches in cycle abort handlers
- [06-02]: ValidationError added to cycle abort catches for get_paginated model_validate failures
- [06-03]: Custom loguru sink replaces filter for traceback redaction (filter only sees message, sink sees full output)
- [06-03]: colorize=False on custom sink -- loguru cannot auto-detect terminal on function sinks
- [06-03]: asyncio.Lock on app.state.search_lock serializes scheduler and manual search-now cycles
- [06-03]: Settings validated via SettingsModel(**new_config) before disk write -- invalid config never persisted
- [06-03]: Log redaction refreshed after settings save to pick up changed API keys

### Roadmap Evolution

- Phase 5 added: Security Hardening (CSRF, SSRF, input validation, Docker hardening, CDN removal)
- Phase 6 added: Bug Fixes & Resilience (race conditions, error handling, state recovery, log redaction)
- Phase 7 added: Test Coverage (async path tests for clients, cycles, scheduler, startup)

### Pending Todos

None yet.

### Blockers/Concerns

- Sonarr v3 vs v4 API: startup version check should log version; always set Content-Type: application/json on POST requests to handle v4 strict enforcement
- pageSize ceiling: log total item count fetched each cycle so users can diagnose unexpected truncation on large libraries

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 06-03-PLAN.md
Resume file: None
