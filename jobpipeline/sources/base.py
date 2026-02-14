from __future__ import annotations

from abc import ABC, abstractmethod

from jobpipeline.core.models import SearchProfile, SourceItem


class SourceAdapter(ABC):
    name: str

    @abstractmethod
    def search(self, profile: SearchProfile, max_items: int) -> list[SourceItem]:
        raise NotImplementedError
