from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class SearchProfile:
    name: str
    target_titles: list[str]
    adjacent_titles: list[str]
    location_mode: str
    city: str
    radius_km: int
    experience_min_years: int
    experience_max_years: int
    must_have_keywords: list[str]
    nice_to_have_keywords: list[str]
    exclude_keywords: list[str]
    time_window_days: int
    master_resume_skills: list[str]


@dataclass(slots=True)
class SourceItem:
    job_url: str
    source_name: str
    source_domain: str
    snippet_meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalJob:
    job_id: str
    source_domain: str
    source_name: str
    job_url: str
    canonical_url: str
    apply_url: str | None
    title: str
    company: str
    location_text: str
    remote_flag: str
    employment_type: str
    posted_date: str | None
    collected_at: str
    description_raw: str
    salary_text: str | None
    skills_extracted: list[str]
    fetch_status: str
    failure_reason: str | None
    first_seen: str
    last_seen: str
    repost_count: int
    merged_from: list[str]
    fit_score: int
    fit_grade: str
    fit_notes: str
    missing_must_have: list[str]
    flags: list[str]
    user_status: str = "New"
    user_notes: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat()
