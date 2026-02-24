"""Web UI routes for Fetcharr dashboard and settings.

Provides the main dashboard page with htmx-polling app cards and search log,
a settings placeholder, and partial endpoints for htmx fragment updates.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

_PKG_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = _PKG_DIR / "templates"
STATIC_DIR = _PKG_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


def _build_app_context(request: Request, app_name: str) -> dict | None:
    """Build a template context dict for a single app.

    Returns None if the app is not enabled in settings.

    Args:
        request: The incoming FastAPI request (used to access app.state).
        app_name: One of "radarr" or "sonarr".

    Returns:
        Dict with name, last_run, next_run, missing_cursor, cutoff_cursor
        or None if app is not enabled.
    """
    settings = request.app.state.settings
    app_config = getattr(settings, app_name, None)
    if app_config is None or not app_config.enabled:
        return None

    state = request.app.state.fetcharr_state
    app_state = state.get(app_name, {})

    # Determine next_run from scheduler job
    next_run = None
    scheduler = request.app.state.scheduler
    job = scheduler.get_job(f"{app_name}_search")
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()

    return {
        "name": app_name,
        "last_run": app_state.get("last_run"),
        "next_run": next_run,
        "missing_cursor": app_state.get("missing_cursor", 0),
        "cutoff_cursor": app_state.get("cutoff_cursor", 0),
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the dashboard page with app status cards and search log."""
    apps: list[dict] = []
    for name in ("radarr", "sonarr"):
        ctx = _build_app_context(request, name)
        if ctx is not None:
            apps.append(ctx)

    state = request.app.state.fetcharr_state
    search_log = state.get("search_log", [])

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"apps": apps, "search_log": search_log},
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    """Render the placeholder settings page."""
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={},
    )


@router.get("/partials/app-card/{app_name}", response_class=HTMLResponse)
async def partial_app_card(request: Request, app_name: str) -> HTMLResponse:
    """Return an HTML fragment for a single app status card (htmx partial)."""
    app_data = _build_app_context(request, app_name)
    if app_data is None:
        return HTMLResponse("")

    return templates.TemplateResponse(
        request=request,
        name="partials/app_card.html",
        context={"app": app_data},
    )


@router.get("/partials/search-log", response_class=HTMLResponse)
async def partial_search_log(request: Request) -> HTMLResponse:
    """Return an HTML fragment for the search log (htmx partial)."""
    state = request.app.state.fetcharr_state
    search_log = state.get("search_log", [])

    return templates.TemplateResponse(
        request=request,
        name="partials/search_log.html",
        context={"search_log": search_log},
    )
