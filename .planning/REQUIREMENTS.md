# Requirements: Fetcharr

**Defined:** 2026-02-23
**Core Value:** Reliably trigger searches in Radarr and Sonarr for missing and upgrade-eligible media on a schedule, without exposing credentials or expanding attack surface.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Connections

- [x] **CONN-01**: User can configure Radarr connection via URL + API key, validated on startup
- [x] **CONN-02**: User can configure Sonarr connection via URL + API key, validated on startup

### Search Engine

- [ ] **SRCH-01**: Fetcharr fetches wanted (missing) items from Radarr
- [ ] **SRCH-02**: Fetcharr fetches cutoff unmet items from Radarr
- [ ] **SRCH-03**: Fetcharr fetches wanted (missing) items from Sonarr
- [ ] **SRCH-04**: Fetcharr fetches cutoff unmet items from Sonarr
- [ ] **SRCH-05**: Fetcharr cycles through items sequentially via round-robin, wrapping to start
- [ ] **SRCH-06**: Sonarr searches trigger at season level using SeasonSearch command
- [ ] **SRCH-07**: Missing and cutoff queues are separate per app with independent cursors
- [ ] **SRCH-08**: Round-robin cursor positions persist across container restarts
- [x] **SRCH-09**: Unmonitored items are filtered out before adding to search queue
- [ ] **SRCH-10**: Future air date items are filtered out of Sonarr queues
- [x] **SRCH-11**: Search log entries show human-readable item names, not just IDs

### Configuration

- [x] **CONF-01**: User can configure number of items to search per cycle, per app (separate missing/cutoff counts)
- [x] **CONF-02**: User can configure search interval per app

### Web UI

- [ ] **WEBU-01**: Dashboard shows last run time and next scheduled run per app
- [ ] **WEBU-02**: Dashboard shows recent search history with item names and timestamps
- [ ] **WEBU-03**: Dashboard shows current round-robin queue position per app
- [ ] **WEBU-04**: Dashboard shows wanted and cutoff unmet item counts per app
- [ ] **WEBU-05**: User can edit all settings via web UI config editor without file editing
- [ ] **WEBU-06**: Dashboard shows connection status with "unreachable since" when *arr is down
- [ ] **WEBU-07**: User can enable/disable each app via toggle without changing other config
- [ ] **WEBU-08**: User can trigger an immediate search cycle per app via "search now" button

### Security

- [x] **SECR-01**: API keys are stored server-side only and never returned by any HTTP endpoint

### Deployment

- [ ] **DEPL-01**: Fetcharr runs as a Docker container with docker-compose support

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Extended Search

- **SRCH-12**: Configurable hard limit / safety ceiling on max items per cycle
- **SRCH-13**: Persistent search history beyond in-memory log (SQLite storage)

### Documentation

- **DOCS-01**: README documents explicit security model (what is/isn't returned by endpoints)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| User accounts / authentication | No auth = no passwords to store = no credential attack surface. Run on Tailscale or behind VPN. |
| Lidarr / Readarr / other *arr support | Radarr + Sonarr cover the primary use case. Each new app adds API complexity. |
| Multi-instance support | Single Radarr + single Sonarr matches user's setup. Run two containers if needed. |
| Notifications (Discord, Telegram, Apprise) | Web UI log is sufficient. Adds dependency and config surface area. |
| Prowlarr integration / indexer stats | Indexer management is out of scope. Use Prowlarr's own UI. |
| Download queue management | *arr apps manage their own queues. Out of search automation scope. |
| Stalled download detection (Swaparr) | Completely outside search automation scope. Use decluttarr. |
| Media discovery / TMDB browsing | This is Overseerr's job, not a search tool's. |
| Storage monitoring | *arr apps refuse imports when disk is full. Edge case optimization. |
| RSS feed monitoring | *arr apps already do RSS sync natively. This tool fills the backlog. |
| OAuth / SSO | No accounts means no auth flows needed. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONN-01 | Phase 1 | Complete |
| CONN-02 | Phase 1 | Complete |
| SECR-01 | Phase 1 | Complete |
| SRCH-01 | Phase 2 | Pending |
| SRCH-02 | Phase 2 | Pending |
| SRCH-03 | Phase 2 | Pending |
| SRCH-04 | Phase 2 | Pending |
| SRCH-05 | Phase 2 | Pending |
| SRCH-06 | Phase 2 | Pending |
| SRCH-07 | Phase 2 | Pending |
| SRCH-08 | Phase 2 | Pending |
| SRCH-09 | Phase 2 | Complete |
| SRCH-10 | Phase 2 | Pending |
| SRCH-11 | Phase 2 | Complete |
| CONF-01 | Phase 2 | Complete |
| CONF-02 | Phase 2 | Complete |
| WEBU-01 | Phase 3 | Pending |
| WEBU-02 | Phase 3 | Pending |
| WEBU-03 | Phase 3 | Pending |
| WEBU-04 | Phase 3 | Pending |
| WEBU-05 | Phase 3 | Pending |
| WEBU-06 | Phase 3 | Pending |
| WEBU-07 | Phase 3 | Pending |
| WEBU-08 | Phase 3 | Pending |
| DEPL-01 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 after roadmap creation*
