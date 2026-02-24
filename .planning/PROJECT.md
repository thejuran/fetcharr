# Fetcharr

## What This Is

A lightweight Docker-based tool that automates searches in Radarr and Sonarr for wanted and cutoff unmet items. Configurable round-robin searches at configurable intervals with a dark theme web UI for status monitoring and config editing. Includes CI/CD pipeline, automated GHCR publishing, SQLite search history, and comprehensive documentation. Built with Python/FastAPI and htmx/Jinja2. Zero credential exposure by design.

## Core Value

Reliably trigger searches in Radarr and Sonarr for missing and upgrade-eligible media on a schedule, without exposing credentials or expanding attack surface.

## Requirements

### Validated

- ✓ Connect to Radarr/Sonarr via API key + URL with startup validation — v1.0
- ✓ Fetch wanted (missing) and cutoff unmet items from both apps — v1.0
- ✓ Round-robin through items sequentially with persistent cursors — v1.0
- ✓ Sonarr searches at season level via SeasonSearch command — v1.0
- ✓ Configurable items per cycle and search interval per app — v1.0
- ✓ Web UI dashboard with htmx polling (status, search log, queue position, counts) — v1.0
- ✓ Web UI config editor with masked API keys — v1.0
- ✓ Search-now button for immediate per-app trigger — v1.0
- ✓ Connection health monitoring with "unreachable since" display — v1.0
- ✓ Per-app enable/disable toggle — v1.0
- ✓ API keys never exposed via any HTTP endpoint — v1.0
- ✓ CSRF protection via Origin/Referer middleware — v1.0
- ✓ SSRF validation, input clamping, config file permissions — v1.0
- ✓ Docker deployment with PUID/PGID, least-privilege, HEALTHCHECK — v1.0
- ✓ State recovery, schema migration, race condition serialization — v1.0
- ✓ 115 tests covering all async paths — v1.0
- ✓ README with install guide, config reference, and security model — v1.1
- ✓ GitHub Actions CI (pytest, lint, Docker build validation) — v1.1
- ✓ Docker release pipeline — dev tag on push, latest + version on release (ghcr.io) — v1.1
- ✓ Local deep code review convention (Claude offers /deep-review before push) — v1.1
- ✓ Configurable hard limit / safety ceiling on max items per cycle — v1.1
- ✓ Persistent search history beyond in-memory log (SQLite storage) — v1.1

### Active

(None — planning next milestone)

### Out of Scope

- User accounts / authentication — local network tool, no auth needed
- Lidarr / Readarr / other *arr support — Radarr + Sonarr only
- Multi-instance support — single Radarr + single Sonarr
- Notifications (Discord, Telegram, Apprise) — web UI log sufficient
- Prowlarr / indexer management — uses existing *arr search infrastructure
- Download queue management — *arr apps handle this
- Media discovery / TMDB browsing — Overseerr's job
- OAuth / SSO — no accounts means no auth flows
- Mobile app — web UI sufficient

## Context

Shipped v1.1 with ~4,012 Python LOC. 115+ tests passing.
Tech stack: Python 3.13, FastAPI, httpx, Pydantic, APScheduler, aiosqlite, Jinja2, htmx, Tailwind CSS v4, loguru, ruff.
Docker: multi-stage build with pytailwindcss builder, python:3.13-slim production, PUID/PGID entrypoint.
CI/CD: GitHub Actions (pytest, ruff, Docker build validation) + GHCR release workflow.
Registry: ghcr.io/thejuran/fetcharr

Replaces Huntarr's core search functionality without the security liabilities (plaintext passwords, unauthenticated API key exposure, 2FA bypass). Deliberately minimal attack surface.

Known concerns for next milestone:
- Sonarr v3 vs v4 API version detection (currently works via Content-Type header)
- pageSize ceiling logging for large libraries
- Search history UI with filtering/pagination (SRCH-14 deferred from v1.1)

## Constraints

- **Tech stack**: Python (FastAPI) + htmx/Jinja2 — matches user's existing project experience
- **Deployment**: Docker container with docker-compose support
- **Security**: API keys must never be exposed via any HTTP endpoint
- **Scope**: Search automation only — deliberately minimal to reduce attack surface

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python/FastAPI over Go | User familiarity, faster iteration | ✓ Good — built in 2 days |
| htmx/Jinja2 over React SPA | Lightweight, no build step, server-rendered | ✓ Good — simple, fast |
| Season-level Sonarr search | Avoids hammering indexers with full-show searches | ✓ Good |
| Round-robin over random | Ensures every item gets searched eventually | ✓ Good |
| No auth | No user accounts = no passwords to store | ✓ Good — core security decision |
| Single instance per app | Simpler config, matches user's setup | ✓ Good |
| APScheduler 3.x over 4.x | 4.x still alpha, 3.x stable with AsyncIOScheduler | ✓ Good |
| JSON state over SQLite | Simpler for cursor + bounded log | ✓ Good — schema migration added in v1.0 |
| Origin/Referer CSRF over tokens | No auth/sessions means no cookies to protect | ✓ Good |
| Vendored htmx over CDN | Reproducible builds, no external dependency | ✓ Good |
| Custom loguru sink for redaction | Filter only sees message, sink sees full output including tracebacks | ✓ Good |
| Ruff rule sets E,F,I,UP,B,SIM | Comprehensive but non-noisy linting | ✓ Good — caught 32 violations at adoption |
| Three parallel CI jobs | No inter-job deps for fastest feedback | ✓ Good |
| docker/metadata-action for tags | Avoids manual shell scripting for GHCR tags | ✓ Good |
| BuildKit GHA cache | Faster Docker rebuilds in CI | ✓ Good |
| Proportional hard max split | floor(missing/total*max) for missing, remainder for cutoff | ✓ Good |
| Connection-per-op SQLite | aiosqlite context manager per function call | ✓ Good |
| Auto-prune at 500 rows | DELETE after each insert keeps DB bounded | ✓ Good |
| Docker Compose only install | No docker run or bare-metal instructions | ✓ Good — simplest path |

---
*Last updated: 2026-02-24 after v1.1 milestone*
