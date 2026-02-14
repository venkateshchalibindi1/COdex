# JobPipeline

Local-first Windows desktop job-search and tracking tool. It searches configured sources, collects and normalizes job details, deduplicates, scores fit against a profile/resume skills list, and syncs to an Excel tracker. It never automates job applications.

## Features
- Source search adapters: RSS, Greenhouse public boards, Lever public boards.
- Collector with JSON-LD JobPosting parsing + HTML text fallback.
- SQLite persistence (`jobs`, `job_sources_seen`, `runs`, `run_errors`).
- Canonical URL dedupe + merge behavior.
- Deterministic fit scoring with explainable notes.
- Excel sync/update preserving user `Status` and `Notes`.
- PySide6 desktop UI with run control, filters, detail pane, link open, status/notes editing.

## Project layout
- `jobpipeline/core`: orchestrator + models + CLI
- `jobpipeline/sources`: adapters + source manager + discovery abstraction
- `jobpipeline/collectors`: fetch/parse
- `jobpipeline/dedupe`: dedupe logic
- `jobpipeline/scoring`: fit scoring
- `jobpipeline/storage`: SQLite repository
- `jobpipeline/export`: Excel synchronization
- `jobpipeline/app`: desktop UI
- `tests`: pytest suite

## Setup (Windows PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
```

## Run tests
```powershell
pytest
```

## Run CLI pipeline
```powershell
python -m jobpipeline.core.cli --config config.yaml
```

## Run desktop app
```powershell
python -m jobpipeline.app.main --config config.yaml
```

## Pipeline steps
1. **Search** via configured adapters (plus optional discovery provider abstraction).
2. **Collect** full content and structured fields.
3. **Deduplicate** by canonical URL and merge source sightings.
4. **Score fit** with hard/soft rules and notes.
5. **(Optional)** enrich tags/ATS type (basic ATS markers via source name today).
6. **Sync to Excel** preserving Status/Notes.
7. **Review in UI** and manually apply outside app.

## Config
Edit `config.yaml` to define profile, source lists, limits, and toggles.

## Notes
- Respects non-goals: no CAPTCHA bypass, no login-wall scraping automation.
- Web discovery defaults to disabled and is pluggable via `SearchProvider`.
