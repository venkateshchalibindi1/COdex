# Agent Notes

## Quick commands
- Run tests: `pytest`
- Run CLI pipeline: `python -m jobpipeline.core.cli --config config.yaml`
- Run UI: `python -m jobpipeline.app.main --config config.yaml`

## Conventions
- Keep pipeline logic inside `jobpipeline/core`.
- Storage interactions go through `jobpipeline/storage/repository.py`.
- Do not automate job applications.
