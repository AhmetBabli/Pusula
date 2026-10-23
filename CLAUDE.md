# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Backend (run from the project root, not from `backend/` — `backend.main:app` is a package path):
```bash
python -m backend.main                                    # dev server, http://localhost:8000, reload if DEBUG=true
python -m pytest backend/tests -q                          # full backend suite
python -m pytest backend/tests/test_auth.py -q              # single file
python -m pytest backend/tests/test_auth.py::test_login_success -q   # single test
```
Backend deps: `pip install -r backend/requirements.txt`. No lint/format tool is configured for the backend.

Frontend (run from `frontend/`):
```bash
npm run dev      # Vite dev server, http://localhost:5173, proxies /api and /ws to :8000
npm run build    # tsc --noEmit && vite build — a type error fails the build
npm run lint     # eslint .
```
No frontend test runner is configured.

## Architecture

**Stack**: FastAPI + SQLAlchemy (SQLite, no Alembic — schema changes are raw `ALTER TABLE` run by hand or via the one-off scripts in `backend/scripts/migrate_*.py`, each idempotent and self-backing-up) on the backend; React 19 + Vite + TypeScript (non-strict) on the frontend, no client-side router (single `AppState` string in `App.tsx` switches between onboarding/auth/intake/dashboard; a `?resetToken=` query param on the root path drives the password-reset screen instead of a real route).

**Shared catalog vs. per-user state**: `Job` and `Event` are catalog tables shared across all users (scraped once, shown to everyone). Anything user-specific about a shared row — status, favorite, AI match score, RSVP — lives in a separate `JobUserState` / `EventUserState` table keyed by `(user_id, row_id)`, fetched via `db_helpers.get_or_create_job_state` / `get_or_create_event_state`. Never add a per-user field directly to `Job` or `Event`; a `Job` row does get a nullable `owner_user_id` when it originated from one user's private inbox (an email converted to an opportunity), and `list_jobs`/`get_job` filter on that to keep it private to its owner.

**Auth**: stateless JWT (`backend/auth.py`), but sessions are revocable via a per-user `token_version` column embedded in the token as `"ver"` — `get_current_user` rejects a token whose `ver` doesn't match the current DB value. `/auth/logout` and a successful `/auth/reset-password` both bump `token_version`, invalidating every previously-issued token for that user across all devices. Always mint tokens through `create_user_token(user)`, never call `create_access_token` directly, or the version claim is skipped. Login and forgot-password intentionally run a dummy password check / send an identical response regardless of whether the account exists, to avoid timing- or content-based account enumeration.

**AI calls never silently degrade**: every Gemini-calling function in `backend/ai/` raises `AIServiceError`/`KariyerTimeoutError`/`KariyerValidationError` (from `backend/exceptions.py`) on failure instead of returning a fallback string. A `KariyerAjaniException` handler in `backend/main.py` converts these into proper HTTP status codes. If you add a new AI-backed endpoint, follow this — an earlier version of `generate_cold_email` returned a `"[Hata] ..."` string on failure that got silently emailed to a real company. `backend/ai/gemini_client.py::_call_model_async_json` is the shared helper with retry/timeout for anything that just needs one JSON response from Gemini.

**WebSocket agent orchestration** (`backend/routers/ws.py`, `agents.py`): long-running AI tasks (CV building, outreach drafting, job/event search, career strategy) run as FastAPI `BackgroundTasks` that stream progress over `/ws/agents/{session_id}`. Connections are keyed by `f"{user_id}:{session_id}"`, not `session_id` alone, and `push_agent_event` requires an explicit `user_id` kwarg — this was previously session-only and let one user's socket be hijacked by guessing another user's `session_id`.

**Secrets at rest**: `backend/utils/crypto.py` (Fernet, `ENCRYPTION_KEY`) encrypts stored per-user secrets (Gemini API key, Gmail app password/OAuth refresh token) as SQLAlchemy hybrid properties (see `UserProfile.gemini_api_key`, `EmailAccount.app_password`). `backend/utils/mailer.py` sends system email (e.g. password reset) from the app's own account (`SYSTEM_EMAIL_*` env vars) — distinct from `backend/automation/outreach_agent.py`, which sends from a *student's own* connected Gmail on their behalf.

**Config fails closed** (`backend/config.py`): `DEBUG` defaults to `false`; `ENCRYPTION_KEY` and `SECRET_KEY` are required (raise on startup) whenever `DEBUG` is false, and are otherwise auto-generated per-process with a warning — never rely on an auto-generated `SECRET_KEY` across multiple workers or restarts, it invalidates every issued JWT. `ALLOWED_ORIGINS` (comma-separated) sets CORS in production; it falls back to a placeholder domain (matches nothing) if unset, so CORS fails closed too.

**Background jobs**: `backend/scheduler.py` (APScheduler, in-process) periodically calls `run_job_sync()` (multi-platform job scraping + per-user AI matching, `backend/routers/jobs.py`) and the inbox sync (`backend/routers/inbox.py`). There is no external workflow tool wired up — the `n8n` service some earlier project notes mention was never actually integrated and has been removed.

**Rate limiting**: `slowapi` via `backend/rate_limiter.py`; endpoints that trigger a paid AI call, send real email, or are auth-related carry an explicit `@limiter.limit(...)`.
