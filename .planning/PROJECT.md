# Fetcharr

## What This Is

A lightweight Docker-based tool that automates searches in Radarr and Sonarr for wanted and cutoff unmet items. It performs a configurable number of round-robin searches at configurable intervals, replacing Huntarr's core search functionality without the bloat or security liabilities. Built with Python/FastAPI and a minimal htmx/Jinja2 status UI.

## Core Value

Reliably trigger searches in Radarr and Sonarr for missing and upgrade-eligible media on a schedule, without exposing credentials or expanding attack surface.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Connect to one Radarr instance via API key + URL
- [ ] Connect to one Sonarr instance via API key + URL
- [ ] Fetch wanted (missing) items from Radarr
- [ ] Fetch cutoff unmet items from Radarr
- [ ] Fetch wanted (missing) items from Sonarr
- [ ] Fetch cutoff unmet items from Sonarr
- [ ] Round-robin through items sequentially, cycling back to start
- [ ] Sonarr searches at season level, not entire show
- [ ] Configurable number of items to search per cycle, per app
- [ ] Configurable search interval per app
- [ ] Trigger search commands via Radarr/Sonarr APIs
- [ ] Minimal web UI showing last run time and next scheduled run
- [ ] Web UI showing recent search history log
- [ ] Web UI showing current queue position in round-robin
- [ ] Web UI showing wanted/cutoff unmet item counts
- [ ] Web UI config editor for all settings
- [ ] API keys stored in config only, never exposed via API endpoints
- [ ] Docker container deployment with docker-compose

### Out of Scope

- User accounts / authentication — local network tool, no auth needed
- Lidarr / Readarr / other *arr support — Radarr + Sonarr only
- Prowlarr / indexer management — uses existing *arr search infrastructure
- Download client management — *arr apps handle this
- Media library management — only triggers searches
- Mobile app — web UI sufficient
- Multi-instance support — single Radarr + single Sonarr
- OAuth / SSO — no accounts means no auth flows

## Context

Huntarr provided automated search triggering for *arr applications but was found to have critical security vulnerabilities: plaintext password storage, unauthenticated API endpoints exposing all configured API keys, 2FA bypass, and unauthenticated setup clearing. The maintainer reportedly suppressed security reports.

Fetcharr intentionally limits scope to just search automation — the one feature that was actually useful. No user accounts means no passwords to store. API keys live in server-side config only and are never returned by any endpoint. The minimal surface area is a feature, not a limitation.

The user runs a homelab with Radarr + Sonarr (single instances each) accessed via Tailscale. The tool needs to be a good Docker citizen that fits into an existing *arr stack.

## Constraints

- **Tech stack**: Python (FastAPI) + htmx/Jinja2 — matches user's existing project experience
- **Deployment**: Docker container with docker-compose support
- **Security**: API keys must never be exposed via any HTTP endpoint — this is the whole reason this project exists
- **Scope**: Search automation only — deliberately minimal to reduce attack surface

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python/FastAPI over Go | User familiarity, faster iteration | — Pending |
| htmx/Jinja2 over React SPA | Lightweight, no build step, server-rendered — matches VolvLog approach | — Pending |
| Season-level Sonarr search | Avoids hammering indexers with full-show searches; each season is a separate queue item | — Pending |
| Round-robin over random | Ensures every item gets searched eventually, predictable behavior | — Pending |
| No auth | No user accounts = no passwords to store = no credential exposure risk | — Pending |
| Single instance per app | Simpler config, matches user's setup | — Pending |

---
*Last updated: 2026-02-23 after initialization*
