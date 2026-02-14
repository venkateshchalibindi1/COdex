from __future__ import annotations

import json
import logging
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from jobpipeline.core.models import CanonicalJob, SourceItem
from jobpipeline.utils.text import canonicalize_url, normalize_whitespace, tokenize_skills
from jobpipeline.utils.throttle import DomainThrottle

logger = logging.getLogger(__name__)


class JobCollector:
    def __init__(self, per_domain_delay_seconds: int, max_retries: int) -> None:
        self.throttle = DomainThrottle(delay_seconds=per_domain_delay_seconds)
        self.max_retries = max_retries

    def collect(self, item: SourceItem) -> CanonicalJob:
        domain = urlparse(item.job_url).netloc
        self.throttle.wait(domain)
        now = datetime.utcnow().replace(microsecond=0).isoformat()

        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.get(item.job_url, timeout=20, follow_redirects=True)
                response.raise_for_status()
                return self._parse_success(item, response.text, str(response.url), now)
            except Exception as exc:  # noqa: BLE001
                if attempt == self.max_retries:
                    logger.warning("collect_failed", extra={"extra_fields": {"url": item.job_url}})
                    return self._failed_job(item, now, str(exc))
        return self._failed_job(item, now, "unknown")

    def _parse_success(self, item: SourceItem, html: str, final_url: str, now: str) -> CanonicalJob:
        soup = BeautifulSoup(html, "html.parser")
        data = self._parse_json_ld(soup)
        title = data.get("title") or soup.title.get_text(strip=True) if soup.title else "Unknown title"
        company = data.get("hiringOrganization", {}).get("name") if isinstance(data.get("hiringOrganization"), dict) else data.get("company")
        company = company or "Unknown company"
        location = data.get("jobLocation", {}).get("address", {}).get("addressLocality") if isinstance(data.get("jobLocation"), dict) else data.get("location")
        location = location or "Unknown"
        description = normalize_whitespace(BeautifulSoup(data.get("description", "") or html, "html.parser").get_text(" "))
        posted = data.get("datePosted")
        apply_url = data.get("url") or final_url
        canonical_url = canonicalize_url(final_url)
        job_id = self._make_job_id(canonical_url, company, title, location)
        remote_flag = "Y" if "remote" in f"{title} {location} {description}".lower() else "Unknown"
        return CanonicalJob(
            job_id=job_id,
            source_domain=item.source_domain,
            source_name=item.source_name,
            job_url=item.job_url,
            canonical_url=canonical_url,
            apply_url=apply_url,
            title=title,
            company=company,
            location_text=location,
            remote_flag=remote_flag,
            employment_type="Unknown",
            posted_date=posted,
            collected_at=now,
            description_raw=description,
            salary_text=None,
            skills_extracted=tokenize_skills(description),
            fetch_status="success",
            failure_reason=None,
            first_seen=now,
            last_seen=now,
            repost_count=0,
            merged_from=[],
            fit_score=0,
            fit_grade="D",
            fit_notes="Not scored yet",
            missing_must_have=[],
            flags=[],
        )

    @staticmethod
    def _parse_json_ld(soup: BeautifulSoup) -> dict:
        for script in soup.select("script[type='application/ld+json']"):
            try:
                payload = json.loads(script.text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, list):
                for node in payload:
                    if isinstance(node, dict) and node.get("@type") == "JobPosting":
                        return node
            if isinstance(payload, dict) and payload.get("@type") == "JobPosting":
                return payload
        return {}

    @staticmethod
    def _make_job_id(canonical_url: str, company: str, title: str, location: str) -> str:
        import hashlib

        raw = f"{canonical_url}|{company.lower()}|{title.lower()}|{location.lower()}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def _failed_job(self, item: SourceItem, now: str, reason: str) -> CanonicalJob:
        canonical_url = canonicalize_url(item.job_url)
        job_id = self._make_job_id(canonical_url, "unknown", "unknown", "unknown")
        return CanonicalJob(
            job_id=job_id,
            source_domain=item.source_domain,
            source_name=item.source_name,
            job_url=item.job_url,
            canonical_url=canonical_url,
            apply_url=None,
            title="Unknown",
            company="Unknown",
            location_text="Unknown",
            remote_flag="Unknown",
            employment_type="Unknown",
            posted_date=None,
            collected_at=now,
            description_raw="",
            salary_text=None,
            skills_extracted=[],
            fetch_status="failed",
            failure_reason=reason,
            first_seen=now,
            last_seen=now,
            repost_count=0,
            merged_from=[],
            fit_score=0,
            fit_grade="D",
            fit_notes="Collection failed",
            missing_must_have=[],
            flags=["collect_failed"],
        )
