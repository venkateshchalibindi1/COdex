from __future__ import annotations

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> list[str]:
        raise NotImplementedError


class DisabledProvider(SearchProvider):
    def search(self, query: str) -> list[str]:
        return []
