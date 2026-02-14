from __future__ import annotations

from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from jobpipeline.core.models import SearchProfile, SourceItem
from jobpipeline.sources.base import SourceAdapter


class GreenhousePublicBoardAdapter(SourceAdapter):
    def __init__(self, board_url: str) -> None:
        self.board_url = board_url.rstrip("/")
        self.name = "Greenhouse"

    def search(self, profile: SearchProfile, max_items: int) -> list[SourceItem]:
        try:
            response = httpx.get(self.board_url, timeout=20)
            response.raise_for_status()
        except httpx.HTTPError:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        found: list[SourceItem] = []
        for link in soup.select("a[href*='/jobs/'], a[href*='gh_jid']"):
            href = link.get("href")
            if not href:
                continue
            full_url = urljoin(self.board_url, href)
            domain = urlparse(full_url).netloc
            found.append(
                SourceItem(
                    job_url=full_url,
                    source_name=self.name,
                    source_domain=domain,
                    snippet_meta={"board": self.board_url},
                )
            )
            if len(found) >= max_items:
                break
        return found
