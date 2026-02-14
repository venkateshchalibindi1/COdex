from __future__ import annotations

from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import httpx

from jobpipeline.core.models import SearchProfile, SourceItem
from jobpipeline.sources.base import SourceAdapter


class GenericRSSAdapter(SourceAdapter):
    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self.url = url

    def search(self, profile: SearchProfile, max_items: int) -> list[SourceItem]:
        try:
            response = httpx.get(self.url, timeout=20)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        root = ET.fromstring(response.text)
        items: list[SourceItem] = []
        for node in root.findall(".//item")[:max_items]:
            link = (node.findtext("link") or "").strip()
            title = (node.findtext("title") or "").strip()
            if not link:
                continue
            domain = urlparse(link).netloc
            items.append(
                SourceItem(
                    job_url=link,
                    source_name=self.name,
                    source_domain=domain,
                    snippet_meta={"feed_title": title},
                )
            )
        return items
