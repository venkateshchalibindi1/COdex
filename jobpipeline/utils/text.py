from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


NOISE_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref"}


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k not in NOISE_PARAMS]
    clean = parsed._replace(query=urlencode(query), fragment="")
    return urlunparse(clean)


def extract_years_requirement(text: str) -> int | None:
    match = re.search(r"(\d+)\+?\s+years", text.lower())
    if match:
        return int(match.group(1))
    return None


def tokenize_skills(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#\-.]{1,30}", text.lower())
    return sorted(set(tokens))
