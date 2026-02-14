from __future__ import annotations

from jobpipeline.core.models import SearchProfile, SourceItem
from jobpipeline.sources.base import SourceAdapter
from jobpipeline.sources.discovery import SearchProvider


class SourceManager:
    def __init__(
        self,
        adapters: list[SourceAdapter],
        exclude_domains: list[str] | None = None,
        provider: SearchProvider | None = None,
    ) -> None:
        self.adapters = adapters
        self.exclude_domains = set(exclude_domains or [])
        self.provider = provider

    def search(self, profile: SearchProfile, max_jobs: int) -> list[SourceItem]:
        items: list[SourceItem] = []
        per_adapter = max(1, max_jobs // max(1, len(self.adapters)))
        for adapter in self.adapters:
            items.extend(adapter.search(profile, per_adapter))
        if self.provider:
            for title in profile.target_titles:
                for url in self.provider.search(title):
                    domain = url.split("/")[2] if "//" in url else ""
                    items.append(SourceItem(job_url=url, source_name="Discovery", source_domain=domain))
        filtered = [item for item in items if item.source_domain not in self.exclude_domains]
        return filtered[:max_jobs]
