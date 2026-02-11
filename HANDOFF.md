# Agent Handoff — PROSIM Web Continuation

## Immediate Issue: Docker Container Failing

The container is crash-looping with a **SQLAlchemy table creation error**. The `ai_competitors` table (added by the teacher mode agent) is causing a conflict during startup.

### To Debug
```bash
docker compose logs prosim 2>&1 | grep -A 5 "ERROR\|error\|Exception"
```

The error is `sqlalche.me/e/20/e3q8` — likely a "table already exists" or foreign key issue in `web/database/models.py`. The `AICompetitor` model was added by the `backend-teacher` agent and may have schema issues.

### Files to Check
- `web/database/models.py` — Look at the `AICompetitor` model and its relationship to `GameSession`
- `web/database/session.py` — The `init_db()` function that runs `create_all()`
- `web/app.py` — Lifespan startup that calls `init_db()`

### Fix Approach
1. Read the full error from `docker compose logs prosim`
2. Fix the model definition in `web/database/models.py`
3. Delete the stale volume: `docker volume rm prosim_data` (fresh DB)
4. Rebuild: `docker compose up --build -d`

## Current Docker Setup
- Context: **orbstack** (local dev)
- Dockerfile uses `--chown=prosim:prosim` for file copies (just fixed)
- `docker-compose.yml` has a `version` key that triggers a warning (cosmetic, remove it)
- Port: 8000

## What's Working (verified with Playwright)
- All 3 CSS themes: Win95, Industrial, Academic
- Theme switching via cookie + JS (instant, no reload)
- Game creation flow
- Decision entry form with all DECS fields
- Week processing (submit decisions → simulation → report)
- Authentic PROSIM report format
- Game dashboard with full state display
- Teacher mode routes exist

## What's Left
1. **Fix Docker startup** (the immediate blocker above)
2. **Task #9: Leaderboard system** — Not started. Needs:
   - Database model for rankings
   - Routes for viewing leaderboard
   - Template for display
   - Ranking by Game Efficiency = (Standard Costs / Actual Costs) × 100%
3. **Remove `version: "3.8"` from docker-compose.yml** (deprecated warning)
4. **Run the full test suite** to verify nothing is broken: `.venv/bin/pytest`
5. **Academic theme button contrast** was just improved — verify it looks good in Docker

## Key Files Modified This Session
- `web/static/css/theme-win95.css` — NEW (Win95 theme, ~1020 lines)
- `web/static/css/theme-industrial.css` — NEW (Industrial/SCADA theme, ~1308 lines)
- `web/static/css/theme-academic.css` — NEW (Academic theme, ~700 lines, contrast fix applied)
- `web/templates/pages/decisions.html` — NEW (decision entry form)
- `web/templates/pages/teacher.html` — NEW (teacher mode panel)
- `web/templates/pages/game.html` — Enhanced (417 lines, full state display)
- `web/templates/base.html` — Modified (theme loading, body class)
- `web/templates/components/navbar.html` — Modified (theme selector dropdown)
- `web/routes/game.py` — Modified (decision GET/POST routes added)
- `web/routes/teacher.py` — NEW (teacher mode routes)
- `web/routes/theme.py` — NEW (theme switching route)
- `web/services/teacher_service.py` — NEW
- `web/database/models.py` — Modified (AICompetitor table added)
- `web/app.py` — Modified (theme middleware, teacher router)
- `web/theme.py` — NEW (theme constants)
- `prosim/engine/ai_player.py` — NEW (3 AI strategies)
- `Dockerfile` — Modified (--chown fix)
- `docker-compose.yml` — Existing
- `.dockerignore` — Modified
- `docs/deployment.md` — NEW
- `.claude/skills/playwright-cli/` — NEW (playwright setup)
- `.claude/settings.json` — NEW (playwright permissions)
- `.gitignore` — Modified (playwright-cli artifacts)

## Commands
```bash
# Run locally (no Docker)
.venv/bin/uvicorn web.app:app --reload

# Run in Docker (orbstack context)
docker context use orbstack
docker compose up --build -d
docker compose logs -f prosim

# Run tests
.venv/bin/pytest

# Playwright testing
playwright-cli open http://localhost:8000
playwright-cli screenshot --full-page
playwright-cli close
```
