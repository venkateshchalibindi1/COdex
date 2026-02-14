from __future__ import annotations

import logging
from datetime import datetime

from jobpipeline.collectors.job_collector import JobCollector
from jobpipeline.core.models import SearchProfile
from jobpipeline.dedupe.service import DedupeService
from jobpipeline.export.excel_sync import ExcelSync
from jobpipeline.scoring.service import FitScorer
from jobpipeline.sources.discovery import DisabledProvider
from jobpipeline.sources.greenhouse import GreenhousePublicBoardAdapter
from jobpipeline.sources.lever import LeverPublicBoardAdapter
from jobpipeline.sources.manager import SourceManager
from jobpipeline.sources.rss import GenericRSSAdapter
from jobpipeline.storage.repository import JobRepository

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self, config: dict, repository: JobRepository | None = None) -> None:
        self.config = config
        self.repository = repository or JobRepository()
        self.collector = JobCollector(
            per_domain_delay_seconds=config["collector"]["per_domain_delay_seconds"],
            max_retries=config["collector"]["max_retries"],
        )
        self.scorer = FitScorer()

    def _profile(self) -> SearchProfile:
        payload = self.config["profiles"][0]
        return SearchProfile(**payload)

    def _source_manager(self) -> SourceManager:
        adapters = [GenericRSSAdapter(feed["name"], feed["url"]) for feed in self.config["sources"]["rss_feeds"]]
        adapters.extend(GreenhousePublicBoardAdapter(url) for url in self.config["sources"].get("greenhouse_boards", []))
        adapters.extend(LeverPublicBoardAdapter(url) for url in self.config["sources"].get("lever_boards", []))
        provider = DisabledProvider()
        return SourceManager(adapters, self.config["filters"]["exclude_domains"], provider)

    def run(self) -> dict[str, int]:
        started = datetime.utcnow().replace(microsecond=0).isoformat()
        run_id = self.repository.create_run(started)
        profile = self._profile()
        manager = self._source_manager()
        max_jobs = self.config["limits"]["max_jobs_per_run"]

        found = manager.search(profile, max_jobs=max_jobs)
        collected = [self.collector.collect(item) for item in found]
        unique_jobs, merged = DedupeService.dedupe(collected)

        failed = 0
        for job in unique_jobs:
            if job.fetch_status != "success":
                failed += 1
                self.repository.add_run_error(run_id, job.source_domain, job.failure_reason or "unknown")
            scored = self.scorer.score(job, profile, self.config["filters"]["seniority_mode"])
            self.repository.upsert_job(scored)

        exported = ExcelSync(self.config["excel_path"]).sync(unique_jobs)
        finished = datetime.utcnow().replace(microsecond=0).isoformat()
        counts = {
            "found": len(found),
            "collected": len(collected),
            "failed": failed,
            "merged": merged,
            "exported": exported,
        }
        self.repository.finish_run(run_id, finished, counts)
        logger.info("run_completed", extra={"extra_fields": counts})
        return counts
