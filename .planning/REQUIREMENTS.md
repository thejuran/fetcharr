# Requirements: Fetcharr

**Defined:** 2026-02-24
**Core Value:** Reliably trigger searches in Radarr and Sonarr for missing and upgrade-eligible media on a schedule, without exposing credentials or expanding attack surface.

## v1.2 Requirements

Requirements for v1.2 Polish & Harden. Each maps to roadmap phases.

### Search Resilience

- [x] **SRCH-15**: Fetcharr detects Sonarr v3 vs v4 API version at startup and logs it
- [x] **SRCH-16**: Fetcharr logs total item count fetched per cycle so users can diagnose pageSize truncation
- [ ] **SRCH-17**: Sonarr episode-by-episode fallback triggers automatically when SeasonSearch fails

### Dashboard & UI

- [ ] **WEBU-09**: Dashboard position labels show "X of Y" (e.g., "3 of 47") instead of bare cursor number
- [x] **WEBU-10**: Dashboard displays recent application log messages (loguru output) in a dedicated section
- [ ] **WEBU-11**: Search log entries show detail/outcome information (not just item name and timestamp)

### Search History

- [ ] **SRCH-14**: User can browse search history with filtering by app/queue type and pagination

### CI/CD

- [x] **CICD-04**: CI workflow pushed to GitHub and tests pass on remote runners

## Future Requirements

Deferred to future release. Tracked but not in current roadmap.

### Notifications

- **NOTF-01**: User receives alerts (Discord, Pushover, etc.) on search errors or cycle summaries

### Multi-Instance

- **MULTI-01**: User can configure multiple Radarr and/or Sonarr instances

## Out of Scope

| Feature | Reason |
|---------|--------|
| User accounts / authentication | Local network tool, no auth needed |
| Lidarr / Readarr / other *arr support | Radarr + Sonarr only for now |
| Prowlarr / indexer management | Uses existing *arr search infrastructure |
| Download queue management | *arr apps handle this |
| Media discovery / TMDB browsing | Overseerr's job |
| OAuth / SSO | No accounts means no auth flows |
| Mobile app | Web UI sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SRCH-14 | Phase 15 | Pending |
| SRCH-15 | Phase 13 | Complete |
| SRCH-16 | Phase 13 | Complete |
| SRCH-17 | Phase 16 | Pending |
| WEBU-09 | Phase 14 | Pending |
| WEBU-10 | Phase 14 | Complete |
| WEBU-11 | Phase 14 | Pending |
| CICD-04 | Phase 13 | Complete |

**Coverage:**
- v1.2 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after roadmap creation*
