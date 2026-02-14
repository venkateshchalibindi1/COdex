from __future__ import annotations

import os
from pathlib import Path

from jobpipeline.app.main import JobPipelineWindow


def test_ui_launches(qtbot, tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
excel_path: data/test.xlsx
profiles:
  - name: default
    target_titles: ["IT Support Specialist"]
    adjacent_titles: []
    location_mode: "Remote"
    city: ""
    radius_km: 0
    experience_min_years: 1
    experience_max_years: 3
    must_have_keywords: ["troubleshooting"]
    nice_to_have_keywords: []
    exclude_keywords: []
    time_window_days: 7
    master_resume_skills: ["troubleshooting"]
sources:
  rss_feeds: []
  greenhouse_boards: []
  lever_boards: []
discovery:
  enabled: false
  provider: disabled
  api_key: ""
collector:
  use_playwright: false
  per_domain_delay_seconds: 0
  max_retries: 0
filters:
  exclude_domains: []
  exclude_keywords: []
  seniority_mode: downrank
limits:
  max_jobs_per_run: 10
        """,
        encoding="utf-8",
    )
    win = JobPipelineWindow(str(cfg))
    qtbot.addWidget(win)
    assert win.windowTitle() == "JobPipeline"
