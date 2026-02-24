# Roadmap: Fetcharr

## Overview

Fetcharr is a single-process automation daemon that cycles through Radarr and Sonarr's wanted/cutoff-unmet lists on a configurable schedule. The build order is dictated by the dependency graph: foundation infrastructure must be correct before the search engine is built on top of it, the web UI reads state produced by the search engine, and Docker packages a working application last. Security invariants (no API key in any HTTP response) are established in Phase 1 and never relaxed.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Config, state, and API clients with security invariants established
- [x] **Phase 2: Search Engine** - Scheduler, round-robin, and cycle logic — the core product
- [x] **Phase 3: Web UI** - Status dashboard and config editor backed by real state data
- [x] **Phase 4: Docker** - Multi-stage packaging and release-ready artifact

## Phase Details

### Phase 1: Foundation
**Goal**: Fetcharr can connect to Radarr and Sonarr, validate those connections on startup, fetch paginated wanted/cutoff-unmet lists, and do so without ever exposing an API key in any HTTP response
**Depends on**: Nothing (first phase)
**Requirements**: CONN-01, CONN-02, SECR-01
**Success Criteria** (what must be TRUE):
  1. Fetcharr starts up, validates Radarr and Sonarr connections, and logs success or a clear error message if either is unreachable
  2. Fetcharr can fetch the full paginated wanted (missing) and cutoff-unmet item lists from both Radarr and Sonarr
  3. No HTTP endpoint — including any config or status endpoint — returns an API key value in its response body or headers
  4. All *arr API calls use X-Api-Key header auth; no API key ever appears in a URL or log line
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffolding, config models (Pydantic + TOML), logging with redaction, and atomic JSON state store
- [x] 01-02-PLAN.md — httpx API clients (base + Radarr + Sonarr) with paginated list fetching and retry logic
- [x] 01-03-PLAN.md — Startup orchestration (entry point, validation, banner) and test suite

### Phase 2: Search Engine
**Goal**: Fetcharr automatically cycles through wanted and cutoff-unmet items for both apps on a configurable schedule, with round-robin position persisted across restarts and Sonarr searching at season level
**Depends on**: Phase 1
**Requirements**: SRCH-01, SRCH-02, SRCH-03, SRCH-04, SRCH-05, SRCH-06, SRCH-07, SRCH-08, SRCH-09, SRCH-10, SRCH-11, CONF-01, CONF-02
**Success Criteria** (what must be TRUE):
  1. Fetcharr triggers MoviesSearch commands for Radarr wanted and cutoff-unmet items on a configurable interval, cycling sequentially through the list
  2. Fetcharr triggers SeasonSearch commands for Sonarr at season level (not series or episode level), deduplicating episode records to unique (seriesId, seasonNumber) pairs before searching
  3. Missing and cutoff-unmet queues are independent with separate cursors per app; advancing one does not affect the other
  4. Round-robin cursor positions survive a container restart — position is read from the state file on startup, not reset to zero
  5. Unmonitored items and future air date items (Sonarr) are filtered out before being added to any search queue
  6. Search log entries record human-readable item names alongside timestamps, not just internal IDs
**Plans:** 3/3 plans complete

Plans:
- [x] 02-01-PLAN.md — Config extension (search tuning fields), client search methods, and core engine utilities (filtering, batch slicing, search logging)
- [x] 02-02-PLAN.md — Radarr and Sonarr search cycle functions with round-robin cursors, episode-to-season deduplication, and skip-on-failure error handling
- [x] 02-03-PLAN.md — APScheduler integration via FastAPI lifespan, uvicorn entry point, state persistence per cycle, and search engine test suite

### Phase 3: Web UI
**Goal**: Users can view the current automation status, recent search history, and queue positions in a browser, and can edit all settings without touching config files
**Depends on**: Phase 2
**Requirements**: WEBU-01, WEBU-02, WEBU-03, WEBU-04, WEBU-05, WEBU-06, WEBU-07, WEBU-08
**Success Criteria** (what must be TRUE):
  1. The dashboard shows last run time, next scheduled run, current round-robin queue position, and wanted/cutoff-unmet item counts for each app without requiring a page reload (htmx polling)
  2. The dashboard shows recent search history with human-readable item names and timestamps
  3. When Radarr or Sonarr is unreachable, the dashboard shows "unreachable since [time]" rather than silently failing or showing stale data
  4. User can view and edit all settings (URLs, intervals, batch sizes, per-app enable/disable) via a web form and save without editing any file on disk
  5. User can trigger an immediate search cycle for a specific app via a "search now" button in the UI
  6. The config editor never displays API key values — placeholders are shown instead, and keys are only accepted on write
**Plans**: 3/3 plans complete

Plans:
- [x] 03-01-PLAN.md — FastAPI routes and Jinja2 base templates, htmx polling for status dashboard
- [x] 03-02-PLAN.md — Dashboard panels (last run, next run, queue position, item counts, connection status, search log)
- [x] 03-03-PLAN.md — Config editor form (GET with masked keys, POST with PRG pattern, per-app enable/disable toggle, search-now trigger)

### Phase 4: Docker
**Goal**: Fetcharr runs as a Docker container that any self-hoster can pull and run with docker-compose, with config and state on a volume and no credentials baked into the image
**Depends on**: Phase 3
**Requirements**: DEPL-01
**Success Criteria** (what must be TRUE):
  1. `docker compose up` starts Fetcharr and the web UI is reachable in a browser
  2. Config and state files live on a named Docker volume and survive container recreation
  3. No API keys or config values are baked into the Docker image layers — all credentials are runtime-only via the volume-mounted config file
  4. Startup emits a clear error (not a silent hang) if the *arr URLs are configured as localhost (a common Docker networking mistake)
**Plans:** 1/1 plans complete

Plans:
- [x] 04-01-PLAN.md — Multi-stage Dockerfile (pytailwindcss builder + slim production), docker-compose.yml, PUID/PGID entrypoint, HEALTHCHECK, and localhost URL detection

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete | 2026-02-23 |
| 2. Search Engine | 3/3 | Complete    | 2026-02-24 |
| 3. Web UI | 3/3 | Complete | 2026-02-24 |
| 4. Docker | 1/1 | Complete    | 2026-02-24 |
