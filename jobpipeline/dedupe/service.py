from __future__ import annotations

from jobpipeline.core.models import CanonicalJob


class DedupeService:
    @staticmethod
    def dedupe(jobs: list[CanonicalJob]) -> tuple[list[CanonicalJob], int]:
        by_canonical: dict[str, CanonicalJob] = {}
        merged = 0
        for job in jobs:
            existing = by_canonical.get(job.canonical_url)
            if not existing:
                by_canonical[job.canonical_url] = job
                continue
            merged += 1
            existing.last_seen = max(existing.last_seen, job.last_seen)
            existing.repost_count += 1
            existing.merged_from.append(job.job_id)
            if len(job.description_raw) > len(existing.description_raw):
                existing.description_raw = job.description_raw
            if job.source_name not in existing.source_name.split(","):
                existing.source_name = f"{existing.source_name},{job.source_name}"
        return list(by_canonical.values()), merged
